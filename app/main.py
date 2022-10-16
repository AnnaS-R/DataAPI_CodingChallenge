from typing import List, Union

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/data/{customer_id}/{dialog_id}", tags=["data"], response_model=schemas.Message)
def create_message(customer_id: int, dialog_id: int, message_content: schemas.MessageBase,
                   db: Session = Depends(get_db)):
    """This endpoint is used to push each customer's input during their dialogue into the db."""
    message = schemas.MessageCreate(customer_id=customer_id, dialog_id=dialog_id, language=message_content.language,
                                    text=message_content.text)
    db_message = crud.create_message(db=db, customer_id=customer_id, dialog_id=dialog_id, message=message)
    return db_message


@app.post("/consents/{dialog_id}", tags=["consents"], response_model=schemas.Dialog)
def create_consent(dialog_id: int, consent: schemas.ConsentField, db: Session = Depends(get_db)):
    """
    This endpoint is used to give consent for us to store and use the data of the dialog.
    If no dialog messages exist, this is interpreted as an error and the consent is not recorded.
    Consent for a dialog cannot be overwritten.
    """
    dialog = schemas.ConsentCreate(dialog_id=dialog_id, consent=consent.consent)
    db_consent = crud.get_consent(db=db, dialog_id=dialog_id)
    if db_consent:
        raise HTTPException(status_code=404, detail="Consent already recorded.")
    db_dialog_messages = crud.get_dialog_messages(db=db, dialog_id=dialog_id)
    if not db_dialog_messages:
        raise HTTPException(status_code=400, detail="No messages with this dialog id have been recorded.")
    db_dialog = crud.create_consent(db=db, dialog=dialog)
    if not consent.consent:
        delete_attempt = crud.delete_dialog_messages(db=db, dialog_id=dialog_id)
        if not delete_attempt:
            HTTPException(status_code=404, detail="No dialog messages found.")
    return db_dialog


@app.get("/data/", tags=["data"], response_model=List[schemas.Message])
def read_messages(language: Union[str, None] = None, customer_id: Union[int, None] = None,
                  db: Session = Depends(get_db)):
    """
    This endpoint returns all the datapoints:
    - that match the query params (if any)
    - for which we have consent for
    - and sorted by most recent data first (sorted by message_id, which autoincrements)
    """
    messages = crud.get_consented_messages(db=db, language=language, customer_id=customer_id)
    print(messages)
    return messages


# basic getters included for testing

@app.get("/data/message/{message_id}", tags=["data"], response_model=schemas.Message)
def read_message(message_id: int, db: Session = Depends(get_db)):
    """This endpoint retrieves a customer input by message id."""
    db_message = crud.get_message(db=db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    return db_message


@app.get("/consents/{dialog_id}", tags=["consents"], response_model=schemas.Message)
def read_consent(dialog_id: int, db: Session = Depends(get_db)):
    """This endpoint retrieves a consent entry by message id."""
    db_consent = crud.get_consent(db=db, dialog_id=dialog_id)
    if db_consent is None:
        raise HTTPException(status_code=404, detail="Consent entry not found.")
    return db_consent
