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