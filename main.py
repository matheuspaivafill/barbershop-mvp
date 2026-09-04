import re
import os
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import bcrypt

from database import engine, Base, SessionLocal, get_db
from models import Business, Client, Appointment, BlockedSlot
from schemas import BusinessCreate, BusinessLogin, ClientCreate, AppointmentCreate, ScheduleUpdate, BlockedSlotCreate

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY não definida. Configure a variável de ambiente SECRET_KEY "
        "antes de subir o servidor (nunca use uma chave fixa em produção)."
    )
ALGORITHM = "HS256"

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
    message = message.replace("Value error, ", "")
    return JSONResponse(
        status_code=422,
        content={"detail": f"{field}: {message}"}
    )


# Função auxiliar para gerar hash de senha
def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

# Função auxiliar para verificar senha
def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        return False

# Função auxiliar para criar Token JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_business(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado.")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        business_id = payload.get("business_id")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=401, detail="Estabelecimento não encontrado.")
    return business


# --- CADASTRO E LOGIN DO ESTABELECIMENTO ---

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_business(business_data: BusinessCreate, db: Session = Depends(get_db)):
    if db.query(Business).filter(Business.email == business_data.email).first():
        raise HTTPException(status_code=400, detail="Esse e-mail já está cadastrado.")

    if db.query(Business).filter(Business.slug == business_data.slug).first():
        raise HTTPException(status_code=400, detail="Esse link personalizado já está em uso.")

    new_business = Business(
        name=business_data.name,
        email=business_data.email,
        password_hash=hash_password(business_data.password),
        slug=business_data.slug
    )
    db.add(new_business)
    db.commit()
    db.refresh(new_business)

    token = create_access_token({"business_id": new_business.id})
    return {"message": "Conta criada com sucesso!", "token": token, "slug": new_business.slug}


@app.post("/login")
def login(login_data: BusinessLogin, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.email == login_data.email).first()
    if not business or not verify_password(login_data.password, business.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    token = create_access_token({"business_id": business.id})
    return {"message": "Login realizado com sucesso!", "token": token, "slug": business.slug}


@app.get("/business/slug/{slug}")
def get_business_by_slug(slug: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.slug == slug.lower()).first()
    if not business:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")
    return {"id": business.id, "name": business.name, "slug": business.slug}


# --- ROTAS PÚBLICAS DO CLIENTE (Para agendamento na página pública) ---

def digits_only(s: str) -> str:
    return re.sub(r"\D", "", s)


def find_client_by_phone(db: Session, business_id: int, phone: str):
    target = digits_only(phone)
    return next(
        (
            c for c in db.query(Client).filter(Client.business_id == business_id).all()
            if digits_only(c.phone) == target
        ),
        None
    )


@app.get("/client/lookup")
def lookup_client(business_id: int, phone: str, db: Session = Depends(get_db)):
    if len(digits_only(phone)) < 8:
        raise HTTPException(status_code=400, detail="Telefone incompleto.")

    client = find_client_by_phone(db, business_id, phone)
    if not client:
        raise HTTPException(status_code=404, detail="Nenhum cadastro encontrado com esse telefone.")

    return {"client_id": client.id, "name": client.name}


@app.get("/client/appointments")
def client_upcoming_appointments(business_id: int, phone: str, db: Session = Depends(get_db)):
    """Retorna os agendamentos futuros de um cliente nesse estabelecimento,
    identificado pelo telefone. Usado para lembrar o cliente de horários já marcados."""
    client = find_client_by_phone(db, business_id, phone)
    if not client:
        return []

    today = datetime.now().date()
    appointments = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.client_id == client.id
    ).all()

    upcoming = []
    for ap in appointments:
        try:
            ap_date = datetime.strptime(ap.date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if ap_date >= today:
            upcoming.append({"date": ap.date, "time": ap.time})

    upcoming.sort(key=lambda a: (a["date"], a["time"]))
    return upcoming


@app.post("/client", status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == client.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")

    # Se já existe um cliente com esse telefone nesse estabelecimento, não duplica o
    # cadastro — apenas avisa que a pessoa já pode agendar direto no passo 2.
    existing_client = find_client_by_phone(db, client.business_id, client.phone)
    if existing_client:
        return {
            "message": f"Esse telefone já está cadastrado como {existing_client.name}. "
                       f"Pode agendar direto no passo 2, sem cadastrar de novo!",
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


def generate_time_slots(start_time: str, end_time: str, duration_minutes: int = 60) -> list[str]:
    """Gera os horários disponíveis entre o início e o fim, no intervalo configurado."""
    start_h, start_m = map(int, start_time.split(":"))
    end_h, end_m = map(int, end_time.split(":"))

    start_total = start_h * 60 + start_m
    end_total = end_h * 60 + end_m

    slots = []
    current = start_total
    while current + duration_minutes <= end_total:
        h = current // 60
        m = current % 60
        slots.append(f"{h:02d}:{m:02d}")
        current += duration_minutes
    return slots


def get_business_day_blocked(db: Session, business_id: int, date: str) -> bool:
    """Verifica se o DIA INTEIRO está bloqueado pro estabelecimento."""
    return db.query(BlockedSlot).filter(
        BlockedSlot.business_id == business_id,
        BlockedSlot.date == date,
        BlockedSlot.time.is_(None)
    ).first() is not None


@app.get("/available-times/{business_id}/{date}")
def available_times(business_id: int, date: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")

    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use o formato AAAA-MM-DD.")

    if parsed_date < datetime.now().date():
        return []

    working_days = [int(d) for d in business.working_days.split(",")]
    if parsed_date.weekday() not in working_days:
        return []

    if get_business_day_blocked(db, business_id, date):
        return []

    all_times = generate_time_slots(business.start_time, business.end_time, business.slot_duration_minutes)

    appointments_day = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.date == date
    ).all()
    occupied_times = {ap.time for ap in appointments_day}

    blocked_slots_day = db.query(BlockedSlot).filter(
        BlockedSlot.business_id == business_id,
        BlockedSlot.date == date,
        BlockedSlot.time.isnot(None)
    ).all()
    blocked_times = {b.time for b in blocked_slots_day}

    available = [tm for tm in all_times if tm not in occupied_times and tm not in blocked_times]
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

    if digits_only(appointment.phone) != digits_only(client.phone):
        raise HTTPException(
            status_code=403,
            detail="O telefone informado não confere com o cadastro deste cliente."
        )

    try:
        parsed_date = datetime.strptime(appointment.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use o formato AAAA-MM-DD.")

    if parsed_date < datetime.now().date():
        raise HTTPException(status_code=400, detail="Não é possível agendar em uma data passada.")

    working_days = [int(d) for d in business.working_days.split(",")]
    if parsed_date.weekday() not in working_days:
        raise HTTPException(status_code=400, detail="O estabelecimento não atende nesse dia da semana.")

    if get_business_day_blocked(db, business.id, appointment.date):
        raise HTTPException(status_code=400, detail="O estabelecimento não está atendendo nessa data.")

    all_times = generate_time_slots(business.start_time, business.end_time, business.slot_duration_minutes)
    if appointment.time not in all_times:
        raise HTTPException(status_code=400, detail="Horário fora do funcionamento do estabelecimento.")

    slot_blocked = db.query(BlockedSlot).filter(
        BlockedSlot.business_id == business.id,
        BlockedSlot.date == appointment.date,
        BlockedSlot.time == appointment.time
    ).first()
    if slot_blocked:
        raise HTTPException(status_code=400, detail="Esse horário não está disponível.")

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


# --- ROTAS PROTEGIDAS (Área administrativa) ---

@app.get("/clients")
def list_clients(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    clients = db.query(Client).filter(Client.business_id == current_business.id).all()
    return [{"id": c.id, "name": c.name, "phone": c.phone} for c in clients]


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
    return {"message": "Cliente removido com sucesso!"}


@app.get("/appointments")
def list_appointments(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    appointments = db.query(Appointment).filter(Appointment.business_id == current_business.id).all()
    result = []
    for ap in appointments:
        client = db.query(Client).filter(Client.id == ap.client_id).first()
        result.append({
            "id": ap.id,
            "client_name": client.name if client else "Cliente removido",
            "date": ap.date,
            "time": ap.time
        })
    return result


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
    return {"message": "Agendamento removido com sucesso!"}


@app.get("/clients/public/{business_id}")
def list_public_clients(business_id: int, db: Session = Depends(get_db)):
    # Removido: essa rota expunha nome de todos os clientes de um estabelecimento
    # publicamente, sem autenticação. Não é mais usada — a identificação do
    # cliente no agendamento agora é feita via /client/lookup, por telefone.
    raise HTTPException(status_code=410, detail="Rota descontinuada.")


# --- CONFIGURAÇÃO DE HORÁRIO DE ATENDIMENTO (Área administrativa) ---

@app.get("/schedule")
def get_schedule(current_business: Business = Depends(get_current_business)):
    return {
        "working_days": current_business.working_days,
        "start_time": current_business.start_time,
        "end_time": current_business.end_time,
        "slot_duration_minutes": current_business.slot_duration_minutes
    }


@app.put("/schedule")
def update_schedule(
    schedule: ScheduleUpdate,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    start_h = int(schedule.start_time.split(":")[0])
    end_h = int(schedule.end_time.split(":")[0])
    if end_h <= start_h:
        raise HTTPException(status_code=400, detail="O horário de término deve ser depois do horário de início.")

    current_business.working_days = schedule.working_days
    current_business.start_time = schedule.start_time
    current_business.end_time = schedule.end_time
    current_business.slot_duration_minutes = schedule.slot_duration_minutes
    db.commit()
    return {"message": "Horário de atendimento atualizado com sucesso!"}


# --- BLOQUEIO DE DIAS E HORÁRIOS (Área administrativa) ---

@app.get("/blocked-slots")
def list_blocked_slots(
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    slots = db.query(BlockedSlot).filter(
        BlockedSlot.business_id == current_business.id
    ).order_by(BlockedSlot.date).all()
    return [
        {"id": s.id, "date": s.date, "time": s.time, "reason": s.reason}
        for s in slots
    ]


@app.post("/blocked-slots", status_code=status.HTTP_201_CREATED)
def create_blocked_slot(
    blocked: BlockedSlotCreate,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    try:
        datetime.strptime(blocked.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use o formato AAAA-MM-DD.")

    existing = db.query(BlockedSlot).filter(
        BlockedSlot.business_id == current_business.id,
        BlockedSlot.date == blocked.date,
        BlockedSlot.time == blocked.time
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Esse dia/horário já está bloqueado.")

    new_block = BlockedSlot(
        business_id=current_business.id,
        date=blocked.date,
        time=blocked.time,
        reason=blocked.reason
    )
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    return {"message": "Bloqueio criado com sucesso!", "id": new_block.id}


@app.delete("/blocked-slots/{block_id}")
def delete_blocked_slot(
    block_id: int,
    current_business: Business = Depends(get_current_business),
    db: Session = Depends(get_db)
):
    block = db.query(BlockedSlot).filter(
        BlockedSlot.id == block_id,
        BlockedSlot.business_id == current_business.id
    ).first()
    if not block:
        raise HTTPException(status_code=404, detail="Bloqueio não encontrado.")

    db.delete(block)
    db.commit()
    return {"message": "Bloqueio removido com sucesso!"}
