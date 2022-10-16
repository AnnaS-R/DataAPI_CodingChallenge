"""Reusable functions to interact with the data in the database."""
from sqlalchemy.orm import Session

from . import models, schemas


def create_message(db: Session, customer_id: int, dialog_id: int, message: schemas.MessageCreate):
    db_message = models.Message(dialog_id=dialog_id, customer_id=customer_id, language=message.language,
                                text=message.text)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def delete_dialog_messages(db: Session, dialog_id: int):
    dialog_messages = db.query(models.Message).filter(models.Message.dialog_id == dialog_id).all()
    if not dialog_messages:
        return False
    db.query(models.Message).filter(models.Message.dialog_id == dialog_id).delete()
    db.commit()
    return True


def get_consented_messages(db: Session, language: str, customer_id: int):
    messages = db.query(models.Message).join(models.Consent).filter(models.Consent.consent).order_by(
        models.Message.id.desc())
    if customer_id:
        messages = messages.filter(models.Message.customer_id == customer_id)
    if language:
        messages = messages.filter(models.Message.language == language)
    return messages.all()


def create_consent(db: Session, dialog: schemas.ConsentCreate):
    db_dialog = models.Consent(dialog_id=dialog.dialog_id, consent=dialog.consent)
    db.add(db_dialog)
    db.commit()
    db.refresh(db_dialog)
    return db_dialog


def get_consent(db: Session, dialog_id: int):
    return db.query(models.Consent).get(dialog_id)


def get_message(db: Session, message_id: int):
    return db.query(models.Message).get(message_id)


def get_dialog_messages(db: Session, dialog_id: int):
    return db.query(models.Message).filter(models.Message.dialog_id == dialog_id).all()
