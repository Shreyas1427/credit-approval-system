# Credit Approval System

This project is a backend system for a credit approval service, built with Django and Django Rest Framework. The entire application is containerized using Docker and uses a PostgreSQL database, a Redis message broker, and Celery for background tasks.

## Features

- **Dockerized Environment**: The entire application stack (web server, database, worker) can be run with a single command.
- **PostgreSQL Database**: Robust and reliable data storage.
- **Background Data Ingestion**: Initial customer and loan data are loaded from Excel files using a Celery background worker to prevent blocking the main application.
- **RESTful API**: A complete set of API endpoints to manage the credit system.
- **Simple Frontend**: A basic user interface to interact with and demonstrate the API's functionality.

---

## API Endpoints

- `POST /api/register/`: Register a new customer.
- `POST /api/check-eligibility/`: Check a customer's loan eligibility based on their credit score.
- `POST /api/create-loan/`: Create a new loan for an eligible customer.
- `GET /api/view-loan/<loan_id>/`: View the details of a specific loan.
- `GET /api/view-loans/<customer_id>/`: View all loans for a specific customer.
- `GET /`: Serves the interactive frontend.

---

## Project Setup and How to Run

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop).

### Step-by-Step Instructions

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd credit-approval-system
    ```

2.  **Build and Start the Docker Containers**
    This command will build the Docker images and start all the services (web server, database, and Celery worker) in the background.
    ```bash
    docker-compose up --build -d
    ```

3.  **Apply Database Migrations**
    This command creates the necessary tables in the PostgreSQL database.
    ```bash
    docker-compose exec web python manage.py migrate
    ```

4.  **Ingest Initial Data**
    This command triggers the Celery worker to read the `customer_data.xlsx` and `loan_data.xlsx` files and populate the database.
    ```bash
    docker-compose exec web python manage.py ingest_data
    ```

5.  **Fix Database Sequence (Important)**
    This step synchronizes the database's auto-incrementing ID counter with the ingested data to prevent key collisions.
    ```bash
    docker-compose exec db psql -U credit_user -d credit_db -c "SELECT setval(pg_get_serial_sequence('api_customer', 'customer_id'), (SELECT MAX(customer_id) FROM api_customer));"
    ```

6.  **Access the Application**
    The application is now fully running.
    -   **Frontend Interface**: Open your web browser and go to `http://localhost:8000`
    -   **API Endpoints**: The API is available at `http://localhost:8000/api/`

---

## How to Stop the Application

To stop all running containers, run the following command in your project directory:
```bash
docker-compose down
