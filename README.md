My implementation of the coding challenge to create a Data API service that handles the storage and retrieval of 
customer inputs to the chatbot. The following functionality is implemented:

1. Individual customer inputs of the dialogs can be pushed to be stored in the db.
2. Consent for the further storage and usage of an dialog can be given or declined 
(after the messages of the dialog have been stored)
3. Data (i.e customer inputs) can be retrieved and are ordered by recency.
Only inputs from dialogs that we have explicit consent for are retrieved.
It's possible to filter by customer or language. 


#### Implementation
Implemented as a ORM FastAPI using SQLAlchemy with SQLite as a database.
The structured data lends itself to a relational database and I used SQLite, due to simplicity 
(i.e. it uses a single file: customer_dialogs.db). The database has two tables: one containing the 
customer inputs (messages) and one containing the consents for the dialogs (consents), linked by the dialog id.


##### Notes
- I am assuming the dialog id is unique 
(because the ```POST /consents/:dialogId``` does not take a customer id as an argument)
- I chose to sort the customer inputs by recency using an auto-incremented message id, 
alternatively a timestamp could be used.
- The payload for the endpoint ```POST /consents/:dialogId``` is _{"consent": true/false}_ not only (as written in the problem statement) _true/false_ 

#### Run the application
From inside the project folder follow the steps below:

Activate virtual env: ``` python -m venv . ```  and ``` source bin/activate ``` 
Install requirements: ```pip install -r requirements.txt```\
Run api: ``` python -m uvicorn app.main:app --reload ``` 

#### Test the application

To view the  automatically generated interactive API documentation from FastAPI (Swagger UI) visit:
 ``` http://localhost:8000/docs``` \
To run the tests: ``` pytest app/tests.py ``` 

