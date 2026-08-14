from pydantic import BaseModel, EmailStr

# Esquemas para a Empresa / Estabelecimento
class BusinessCreate(BaseModel):
    name: str
    email: str
    password: str
    slug: str

class BusinessLogin(BaseModel):
    email: str
    password: str

# Esquemas para Cliente
class ClientCreate(BaseModel):
    business_id: int
    name: str
    phone: str

# Esquemas para Agendamento
class AppointmentCreate(BaseModel):
    business_id: int
    client_id: int
    date: str
    time: str