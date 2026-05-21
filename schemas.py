from pydantic import BaseModel

class ClientCreate(BaseModel):
    name: str
    phone: str

class AppointmentCreate(BaseModel):
    client_id: int
    date: str
    time: str