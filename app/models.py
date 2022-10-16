from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Consent(Base):
    __tablename__ = "consents"

    dialog_id = Column(Integer, primary_key=True, index=True)
    consent = Column(Boolean, default=False, index=True)

    messages = relationship("Message", back_populates="consent")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    dialog_id = Column(Integer, ForeignKey("consents.dialog_id"))
    customer_id = Column(Integer, index=True)
    language = Column(String, index=True)
    text = Column(String, index=True)

    consent = relationship("Consent", back_populates="messages")
