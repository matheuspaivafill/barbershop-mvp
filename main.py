from fastapi import FastAPI
from pydantic import BaseModel
from database import engine
from database import Base
from database import SessionLocal
from models import Client
from models import Appointment
from schemas import ClientCreate, AppointmentCreate
from fastapi.middleware.cors import CORSMiddleware

db = SessionLocal()
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Primeiro teste"}


@app.post("/client")
def create_client(client: ClientCreate):
    new_client = Client(
        name=client.name,
        phone=client.phone
    )
        
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return {
    "message": f"O cliente {client.name} foi criado com sucesso! Seu ID é {new_client.id}. Use esse ID para fazer agendamentos."
}



@app.get("/clients")
def list_clients():
    return db.query(Client).all()



@app.post("/appointment")
def create_appointment(appointment: AppointmentCreate):
    existing_appointment = db.query(Appointment).filter(
        Appointment.time == appointment.time,
        Appointment.date == appointment.date
    ).first()
    if existing_appointment:
            return {"Error": "O horário já está ocupado"}
        
    client = db.query(Client).filter(
        Client.id == appointment.client_id
    ).first()
    
    if not client:
            return {"Error": "Id não encontrado!"}
    
    
    new_appointment = Appointment(
    client_id = appointment.client_id,
    date = appointment.date,
    time = appointment.time
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
            
    return {"message": f"O horário para {client.name} foi agendado para {appointment.date} às {appointment.time}", "appointment_id": new_appointment.id}



@app.get("/appointments")
def list_appointments():    
    return db.query(Appointment).all()



@app.delete("/appointment/{appointment_id}")
def delete_appointment(appointment_id: int):
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id  
    ).first()
    if not appointment:
        return {"Error": "Agendamento não encontrado"}
    
    db.delete(appointment)
    db.commit()
    return {"message": f"Agendamento {appointment_id} cancelado com sucesso!"}



@app.get("/appointments/{date}")
def create_schedule(date: str): 

    appointments_day = db.query(Appointment).filter(
        Appointment.date == date
    ).all()
    return appointments_day



@app.get("/available-times/{date}")
def available_times(date: str):
    
    all_times = [
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
    ]

    appointments_day = db.query(Appointment).filter(
         Appointment.date == date
    ).all()

    occupied_times = []

    for ap in appointments_day:
         occupied_times.append(ap.time)

    available_times = []

    for tm in all_times:
         if tm not in occupied_times:
              available_times.append(tm)

    return available_times