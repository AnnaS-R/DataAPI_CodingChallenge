import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app import models

SQLALCHEMY_DATABASE_URL = "sqlite:///app/test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# database starts empty for each test
@pytest.fixture()
def test_db():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


# use test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_message(test_db):
    response = client.post("/data/1/1", json={"language": "EN", "text": "message1"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["language"] == "EN"
    assert data["text"] == "message1"
    assert "id" in data
    message_id = data["id"]

    response = client.get(f"/data/message/{message_id}")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": message_id,
        "language": "EN",
        "text": "message1",
        "customer_id": 1,
        "dialog_id": 1,
    }


def test_create_messages_ordering_same_dialog(test_db):
    response = client.post("/data/1/1", json={"language": "EN", "text": "message1"})
    assert response.status_code == 200, response.text
    id_msg1 = response.json()["id"]
    response = client.post("/data/1/1", json={"language": "EN", "text": "message2"})
    assert response.status_code == 200, response.text
    id_msg2 = response.json()["id"]
    assert id_msg1 < id_msg2


def test_give_consent(test_db):
    # populate db
    response = client.post("/data/3/10", json={"language": "EN", "text": "message1_d1"})
    assert response.status_code == 200, response.text
    id_msg1 = response.json()["id"]
    response = client.post("/data/3/10", json={"language": "EN", "text": "message2_d1"})
    assert response.status_code == 200, response.text
    id_msg2 = response.json()["id"]

    # store the given consent
    response = client.post("/consents/10", json={"consent": True})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["consent"]
    assert data["dialog_id"] == 10

    # check that messages of the dialog are still stored in db
    response = client.get(f"/data/message/{id_msg1}")
    assert response.status_code == 200, response.text
    response = client.get(f"/data/message/{id_msg2}")
    assert response.status_code == 200, response.text


def test_decline_consent(test_db):
    # populate db
    response = client.post("/data/3/10", json={"language": "EN", "text": "message1_d1"})
    assert response.status_code == 200, response.text
    data = response.json()
    id_msg1 = data["id"]
    response = client.post("/data/3/10", json={"language": "EN", "text": "message2_d1"})
    assert response.status_code == 200, response.text
    data = response.json()
    id_msg2 = data["id"]

    # store the declining of consent
    response = client.post("/consents/10", json={"consent": False})
    assert response.status_code == 200, response.text
    data = response.json()
    assert not data["consent"]
    assert data["dialog_id"] == 10

    # check that messages of dialog have been deleted
    response = client.get(f"/data/message/{id_msg1}")
    assert response.status_code == 404, response.text
    response = client.get(f"/data/message/{id_msg2}")
    assert response.status_code == 404, response.text


def test_consent_bad_dialog_id(test_db):
    # decline the storage of a consent entry, if no messages of the dialog have been stored
    # (request may be an error)
    response = client.post("/consents/10", json={"consent": False})
    assert response.status_code == 400, (
        response.text == "No messages with this dialog id have been recorded."
    )


def test_read_messages_no_params(test_db):
    # populate db
    # consent given
    client.post("/data/1/10", json={"language": "EN", "text": "message1_d10"})
    client.post("/data/1/10", json={"language": "EN", "text": "message2_d10"})
    client.post("/consents/10", json={"consent": True})
    # consent declined
    client.post("/data/2/20", json={"language": "FR", "text": "message1_d20"})
    client.post("/data/2/20", json={"language": "FR", "text": "message2_d20"})
    client.post("/consents/20", json={"consent": False})
    # consent not recorded yet
    client.post("/data/3/30", json={"language": "EN", "text": "message1_d30"})
    client.post("/data/3/30", json={"language": "EN", "text": "message2_d30"})

    # test that the returned datapoints match the filters, are ordered and whose use has been consented
    response = client.get("/data/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == [
        {
            "id": 2,
            "language": "EN",
            "text": "message2_d10",
            "customer_id": 1,
            "dialog_id": 10,
        },
        {
            "id": 1,
            "language": "EN",
            "text": "message1_d10",
            "customer_id": 1,
            "dialog_id": 10,
        },
    ]


def test_read_messages_language_param(test_db):
    # populate db
    # consent given
    client.post("/data/1/10", json={"language": "EN", "text": "message1_d10"})
    client.post("/data/1/10", json={"language": "FR", "text": "message2_d10"})
    client.post("/consents/10", json={"consent": True})
    # consent declined
    client.post("/data/2/20", json={"language": "FR", "text": "message1_d20"})
    client.post("/data/2/20", json={"language": "FR", "text": "message2_d20"})
    client.post("/consents/20", json={"consent": False})
    # consent not recorded yet
    client.post("/data/3/30", json={"language": "EN", "text": "message1_d30"})
    client.post("/data/3/30", json={"language": "EN", "text": "message2_d30"})

    # test that the returned datapoints match the filters, are ordered and whose use has been consented
    response = client.get("/data/?language=FR")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == [
        {
            "id": 2,
            "language": "FR",
            "text": "message2_d10",
            "customer_id": 1,
            "dialog_id": 10,
        }
    ]


def test_read_messages_customer_param(test_db):
    # populate db
    # consent given
    client.post("/data/1/10", json={"language": "EN", "text": "message1_d10"})
    client.post("/data/1/10", json={"language": "FR", "text": "message2_d10"})
    client.post("/consents/10", json={"consent": True})
    client.post("/data/4/40", json={"language": "EN", "text": "message1_d40"})
    client.post("/data/4/40", json={"language": "FR", "text": "message2_d40"})
    client.post("/consents/40", json={"consent": True})
    # consent declined
    client.post("/data/2/20", json={"language": "FR", "text": "message1_d20"})
    client.post("/data/2/20", json={"language": "FR", "text": "message2_d20"})
    client.post("/consents/20", json={"consent": False})
    # consent not recorded yet
    client.post("/data/3/30", json={"language": "EN", "text": "message1_d30"})
    client.post("/data/3/30", json={"language": "EN", "text": "message2_d30"})

    # test that the returned datapoints match the filters, are ordered and whose use has been consented
    response = client.get("/data/?customer_id=4")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == [
        {
            "id": 4,
            "language": "FR",
            "text": "message2_d40",
            "customer_id": 4,
            "dialog_id": 40,
        },
        {
            "id": 3,
            "language": "EN",
            "text": "message1_d40",
            "customer_id": 4,
            "dialog_id": 40,
        },
    ]


def test_read_messages_customer_and_language_param(test_db):
    # populate db
    # consent given
    client.post("/data/1/10", json={"language": "EN", "text": "message1_d10"})
    client.post("/data/1/10", json={"language": "FR", "text": "message2_d10"})
    client.post("/consents/10", json={"consent": True})
    client.post("/data/4/40", json={"language": "EN", "text": "message1_d40"})
    client.post("/data/4/40", json={"language": "FR", "text": "message2_d40"})
    client.post("/consents/40", json={"consent": True})
    client.post("/data/4/50", json={"language": "EN", "text": "message1_d50"})
    client.post("/data/4/50", json={"language": "FR", "text": "message2_d50"})
    client.post("/consents/50", json={"consent": True})
    # consent declined
    client.post("/data/2/20", json={"language": "FR", "text": "message1_d20"})
    client.post("/data/2/20", json={"language": "FR", "text": "message2_d20"})
    client.post("/consents/20", json={"consent": False})
    # consent not recorded yet
    client.post("/data/3/30", json={"language": "EN", "text": "message1_d30"})
    client.post("/data/3/30", json={"language": "EN", "text": "message2_d30"})

    # test that the returned datapoints match the filters, are ordered and whose use has been consented
    response = client.get("/data/?language=EN&customer_id=4")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == [
        {
            "id": 5,
            "language": "EN",
            "text": "message1_d50",
            "customer_id": 4,
            "dialog_id": 50,
        },
        {
            "id": 3,
            "language": "EN",
            "text": "message1_d40",
            "customer_id": 4,
            "dialog_id": 40,
        },
    ]


def test_read_messages_empty_response(test_db):
    response = client.get("/data/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data == []
