import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import engine, Base, SessionLocal
from models import Business, Client, Appointment
from schemas import BusinessCreate, BusinessLogin, ClientCreate, AppointmentCreate

# Configurações de Segurança
SECRET_KEY = "sua_chave_secreta_super_segura_mude_em_producao"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cria as tabelas atualizadas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    new_client = Client(
        business_id=client.business_id,
        name=client.name,
        phone=client.phone
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return {"message": "Cliente cadastrado com sucesso!", "client_id": new_client.id}


@app.get("/available-times/{business_id}/{date}")
def available_times(business_id: int, date: str, db: Session = Depends(get_db)):
    all_times = [
        "08:00", "09:00", "10:00", "11:00", "12:00",
        "13:00", "14:00", "15:00", "16:00", "17:00"
    ]

    appointments_day = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.date == date
    ).all()
    
    occupied_times = [ap.time for ap in appointments_day]
    available = [tm for tm in all_times if tm not in occupied_times]
    return available


@app.post("/appointment", status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
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