from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)            # Ex: Barbearia do Zé
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)   # Senha criptografada
    slug = Column(String, unique=True, index=True, nullable=False) # Ex: barbearia-do-ze

    # Relacionamentos
    clients = relationship("Client", back_populates="business")
    appointments = relationship("Appointment", back_populates="business")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)

    # Relacionamentos
    business = relationship("Business", back_populates="clients")
    appointments = relationship("Appointment", back_populates="client")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)

    # Relacionamentos
    business = relationship("Business", back_populates="appointments")
    client = relationship("Client", back_populates="appointments")
