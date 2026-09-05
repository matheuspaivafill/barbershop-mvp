import re
from pydantic import BaseModel, EmailStr, field_validator

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Esquemas para a Empresa / Estabelecimento
class BusinessCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    slug: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        return v

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v):
        v = v.strip().lower()
        if not SLUG_RE.match(v):
            raise ValueError(
                "O link personalizado só pode ter letras minúsculas, números e hífens "
                "(ex: barbearia-do-ze)."
            )
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("O nome do estabelecimento não pode ficar vazio.")
        return v

class BusinessLogin(BaseModel):
    email: EmailStr
    password: str

# Esquemas para Cliente
class ClientCreate(BaseModel):
    business_id: int
    name: str
    phone: str

    @field_validator("name", "phone")
    @classmethod
    def not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Campo obrigatório não pode ficar vazio.")
        return v

# Esquemas para Agendamento
class AppointmentCreate(BaseModel):
    business_id: int
    client_id: int
    phone: str  # confirmação: precisa bater com o telefone cadastrado do cliente
    date: str
    time: str

    @field_validator("phone")
    @classmethod
    def phone_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Informe o telefone para confirmar o agendamento.")
        return v


TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
ALLOWED_DURATIONS = [15, 30, 45, 60, 90, 120]

# Esquemas para configuração de horário de atendimento
class ScheduleUpdate(BaseModel):
    working_days: str  # Ex: "0,1,2,3,4" (0=Segunda ... 6=Domingo)
    start_time: str    # Ex: "08:00"
    end_time: str       # Ex: "18:00"
    slot_duration_minutes: int = 60  # intervalo entre horários disponíveis
    capacity: int = 1  # quantos atendimentos simultâneos (ex: nº de profissionais)

    @field_validator("working_days")
    @classmethod
    def validate_working_days(cls, v):
        v = v.strip()
        if v == "":
            raise ValueError("Selecione pelo menos um dia de atendimento.")
        parts = v.split(",")
        for p in parts:
            if p not in ["0", "1", "2", "3", "4", "5", "6"]:
                raise ValueError("Dias de atendimento inválidos.")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v):
        if not TIME_RE.match(v):
            raise ValueError("Horário inválido. Use o formato HH:MM.")
        return v

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v):
        if v < 1 or v > 20:
            raise ValueError("O número de atendimentos simultâneos deve ser entre 1 e 20.")
        return v

    @field_validator("slot_duration_minutes")
    @classmethod
    def validate_duration(cls, v):
        if v not in ALLOWED_DURATIONS:
            raise ValueError(f"Intervalo inválido. Use um destes: {ALLOWED_DURATIONS}.")
        return v

# Esquemas para bloqueio de dias/horários
class BlockedSlotCreate(BaseModel):
    date: str
    time: str | None = None  # se não informado, bloqueia o dia inteiro
    reason: str | None = None

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v):
        if v is not None and not TIME_RE.match(v):
            raise ValueError("Horário inválido. Use o formato HH:MM.")
        return v
