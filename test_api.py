import requests
import json

# --- Configuration ---
BASE_URL = "http://localhost:8000/api"

def print_response(response):
    """Helper function to print the status code and JSON response."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=4))
    except json.JSONDecodeError:
        print("Response content is not valid JSON.")
        print(response.text)
    print("-" * 50)


def test_register_customer():
    """Tests the /register endpoint."""
    print("--- Testing Customer Registration ---")
    url = f"{BASE_URL}/register/"
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "age": 35,
        "monthly_salary": 75000,
        "phone_number": 9988776655  # Use a unique phone number for each run
    }
    response = requests.post(url, json=payload)
    print(f"POST {url}")
    print_response(response)
    # Return the new customer ID for use in other tests
    if response.status_code == 201:
        return response.json().get('customer_id')
    return None


def test_check_eligibility(customer_id):
    """Tests the /check-eligibility endpoint."""
    if not customer_id:
        print("Skipping eligibility check, no customer ID.")
        return

    print("--- Testing Loan Eligibility ---")
    url = f"{BASE_URL}/check-eligibility/"
    payload = {
        "customer_id": customer_id,
        "loan_amount": 150000,
        "interest_rate": 10.5,
        "tenure": 12
    }
    response = requests.post(url, json=payload)
    print(f"POST {url}")
    print_response(response)


def test_create_loan(customer_id):
    """Tests the /create-loan endpoint."""
    if not customer_id:
        print("Skipping loan creation, no customer ID.")
        return None

    print("--- Testing Loan Creation (Approved) ---")
    url = f"{BASE_URL}/create-loan/"
    payload = {
        "customer_id": customer_id,
        "loan_amount": 50000,
        "interest_rate": 12,
        "tenure": 6
    }
    response = requests.post(url, json=payload)
    print(f"POST {url}")
    print_response(response)
    if response.status_code == 201 and response.json().get('loan_approved'):
        return response.json().get('loan_id')
    return None


def test_view_loan(loan_id):
    """Tests the /view-loan/<loan_id> endpoint."""
    if not loan_id:
        print("Skipping view loan, no loan ID.")
        return

    print("--- Testing View Single Loan ---")
    url = f"{BASE_URL}/view-loan/{loan_id}/"
    response = requests.get(url)
    print(f"GET {url}")
    print_response(response)


def test_view_customer_loans(customer_id):
    """Tests the /view-loans/<customer_id> endpoint."""
    if not customer_id:
        print("Skipping view customer loans, no customer ID.")
        return
    
    # We will use an existing customer from the ingested data for this test
    # to ensure they have loans to view.
    print("--- Testing View All Loans for a Customer (Customer ID: 1) ---")
    customer_id_with_loans = 1
    url = f"{BASE_URL}/view-loans/{customer_id_with_loans}/"
    response = requests.get(url)
    print(f"GET {url}")
    print_response(response)


if __name__ == "__main__":
    # Make sure your Docker containers are running before executing this script.
    
    # 1. Register a new customer
    new_customer_id = test_register_customer()

    # 2. Check eligibility for the new customer
    test_check_eligibility(new_customer_id)

    # 3. Create a new loan for the new customer
    new_loan_id = test_create_loan(new_customer_id)

    # 4. View the details of the newly created loan
    test_view_loan(new_loan_id)

    # 5. View all loans for a pre-existing customer (from ingested data)
    test_view_customer_loans(new_customer_id)
