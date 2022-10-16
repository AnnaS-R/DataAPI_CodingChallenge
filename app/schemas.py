from typing import List
from pydantic import BaseModel


class MessageBase(BaseModel):
    text: str
    language: str


class MessageCreate(MessageBase):
    dialog_id: int
    customer_id: int


class Message(MessageCreate):
    id: int

    class Config:
        orm_mode = True


class ConsentField(BaseModel):
    consent: bool


class ConsentCreate(ConsentField):
    dialog_id: int


class Dialog(ConsentCreate):
    messages: List[Message] = []

    class Config:
        orm_mode = True
