import re
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import engine, Base, SessionLocal
from models import Business, Client, Appointment
from schemas import BusinessCreate, BusinessLogin, ClientCreate, AppointmentCreate

# Configurações de Segurança
import os

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY não definida. Configure a variável de ambiente SECRET_KEY "
        "antes de subir o servidor (nunca use uma chave fixa em produção)."
    )
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Lista de origens autorizadas a chamar a API (troque pelo domínio real em produção)
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://127.0.0.1:5500,http://localhost:5500"
).split(",")

# Cria as tabelas atualizadas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Transforma os erros técnicos de validação (422) em mensagens simples,
# em português, para aparecerem certinho nos toasts do frontend.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    field = first_error["loc"][-1] if first_error.get("loc") else "campo"
    message = first_error.get("msg", "Valor inválido.")
    # Pydantic prefixa mensagens customizadas com "Value error, " — removemos para ficar mais limpo.
    message = message.replace("Value error, ", "")
    return JSONResponse(
        status_code=422,
        content={"detail": f"{field}: {message}"}
    )

# Injeção de dependência do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função auxiliar para gerar hash de senha
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Função auxiliar para verificar senha
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Função auxiliar para criar Token JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7) # Token válido por 7 dias
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Dependência para autenticar a empresa nas rotas protegidas
def get_current_business(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido ou inválido."
        )
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        business_id: int = payload.get("business_id")
        if business_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado ou inválido")
    
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")
    
    return business


# --- ROTAS DE AUTENTICAÇÃO E CADASTRO DA EMPRESA ---

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_business(business_data: BusinessCreate, db: Session = Depends(get_db)):
    # Verifica se e-mail ou slug já existem
    if db.query(Business).filter(Business.email == business_data.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    if db.query(Business).filter(Business.slug == business_data.slug).first():
        raise HTTPException(status_code=400, detail="Link/Slug já em uso. Escolha outro.")

    new_business = Business(
        name=business_data.name,
        email=business_data.email,
        password_hash=hash_password(business_data.password),
        slug=business_data.slug.lower()
    )
    db.add(new_business)
    db.commit()
    db.refresh(new_business)

    token = create_access_token({"business_id": new_business.id})
    return {"message": "Empresa cadastrada com sucesso!", "token": token, "slug": new_business.slug}


@app.post("/login")
def login(login_data: BusinessLogin, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.email == login_data.email).first()
    
    if not business or not verify_password(login_data.password, business.password_hash):
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos.")

    token = create_access_token({"business_id": business.id})
    return {"token": token, "business_name": business.name, "slug": business.slug}


# --- ROTA PÚBLICA (Para identificar a empresa pelo slug no link) ---

@app.get("/business/slug/{slug}")
def get_business_by_slug(slug: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.slug == slug.lower()).first()
    if not business:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"id": business.id, "name": business.name, "slug": business.slug}


# --- ROTAS PÚBLICAS DO CLIENTE (Para agendamento na página pública) ---

@app.post("/client", status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == client.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")

    # Se já existe um cliente com esse telefone nesse estabelecimento, não duplica o
    # cadastro — apenas avisa que a pessoa já pode agendar direto no passo 2.
    digits_only = lambda s: re.sub(r"\D", "", s)
    existing_client = next(
        (
            c for c in db.query(Client).filter(Client.business_id == client.business_id).all()
            if digits_only(c.phone) == digits_only(client.phone)
        ),
        None
    )
    if existing_client:
        return {
            "message": f"Esse telefone já está cadastrado como {existing_client.name}. "
                       f"Pode selecionar seu nome direto no passo 2, sem cadastrar de novo!",
            "client_id": existing_client.id,
            "already_registered": True
        }

    new_client = Client(
        business_id=client.business_id,
        name=client.name,
        phone=client.phone
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return {"message": "Cliente cadastrado com sucesso!", "client_id": new_client.id, "already_registered": False}


ALL_TIMES = [
    "08:00", "09:00", "10:00", "11:00", "12:00",
    "13:00", "14:00", "15:00", "16:00", "17:00"
]


@app.get("/available-times/{business_id}/{date}")
def available_times(business_id: int, date: str, db: Session = Depends(get_db)):
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use o formato AAAA-MM-DD.")

    if parsed_date < datetime.now().date():
        return []

    appointments_day = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.date == date
    ).all()

    occupied_times = [ap.time for ap in appointments_day]
    available = [tm for tm in ALL_TIMES if tm not in occupied_times]
    return available


@app.post("/appointment", status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == appointment.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")

    client = db.query(Client).filter(
        Client.id == appointment.client_id,
        Client.business_id == appointment.business_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado neste estabelecimento.")

    # Confirma que quem está agendando é realmente o dono do cadastro,
    # comparando só os dígitos do telefone (ignora espaços, parênteses e traços).
    digits_only = lambda s: re.sub(r"\D", "", s)
    if digits_only(appointment.phone) != digits_only(client.phone):
        raise HTTPException(
            status_code=403,
            detail="O telefone informado não confere com o cadastro deste cliente."
        )

    if appointment.time not in ALL_TIMES:
        raise HTTPException(status_code=400, detail="Horário inválido.")

    try:
        parsed_date = datetime.strptime(appointment.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use o formato AAAA-MM-DD.")

    if parsed_date < datetime.now().date():
        raise HTTPException(status_code=400, detail="Não é possível agendar em uma data passada.")

    existing = db.query(Appointment).filter(
        Appointment.business_id == appointment.business_id,
        Appointment.date == appointment.date,
        Appointment.time == appointment.time
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Horário já ocupado nesta empresa.")

    new_appointment = Appointment(
        business_id=appointment.business_id,
        client_id=appointment.client_id,
        date=appointment.date,
        time=appointment.time
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return {"message": "Agendamento realizado com sucesso!"}


# --- ROTAS PROTEGIDAS DO ADMIN (Exigem Token da Empresa) ---

@app.get("/clients")
def list_clients(
    current_business: Business = Depends(get_current_business), 
    db: Session = Depends(get_db)
):
    # Retorna apenas os clientes pertencentes à empresa logada
    return db.query(Client).filter(Client.business_id == current_business.id).all()


@app.delete("/client/{client_id}")
def delete_client(
    client_id: int, 
    current_business: Business = Depends(get_current_business), 
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id, 
        Client.business_id == current_business.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    
    db.delete(client)
    db.commit()
    return {"message": "Cliente apagado com sucesso!"}


@app.get("/appointments")
def list_appointments(
    current_business: Business = Depends(get_current_business), 
    db: Session = Depends(get_db)
):
    # Retorna apenas os agendamentos da empresa logada
    return db.query(Appointment).filter(Appointment.business_id == current_business.id).all()


@app.delete("/appointment/{appointment_id}")
def delete_appointment(
    appointment_id: int, 
    current_business: Business = Depends(get_current_business), 
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.business_id == current_business.id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    
    db.delete(appointment)
    db.commit()
    return {"message": "Agendamento cancelado com sucesso!"}

@app.get("/clients/public/{business_id}")
def list_public_clients(business_id: int, db: Session = Depends(get_db)):
    clients = db.query(Client).filter(Client.business_id == business_id).all()
    return [{"id": c.id, "name": c.name} for c in clients]