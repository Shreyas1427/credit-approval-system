import pandas as pd
from celery import shared_task
from .models import Customer, Loan

@shared_task
def ingest_customer_data():
    # Add engine='openpyxl' here
    df = pd.read_excel('customer_data.xlsx', engine='openpyxl')

    for _, row in df.iterrows():
        Customer.objects.update_or_create(
            customer_id=row['Customer ID'], # Match the exact column name from the file
            defaults={
                'first_name': row['First Name'],
                'last_name': row['Last Name'],
                'phone_number': row['Phone Number'],
                'monthly_salary': row['Monthly Salary'],
                'approved_limit': row['Approved Limit'],
                # The 'Current Debt' might not be in the initial file, so use .get
                'current_debt': row.get('Current Debt', 0) 
            }
        )
    return "Customer data ingestion complete."

@shared_task
def ingest_loan_data():
    # Add engine='openpyxl' here
    df = pd.read_excel('loan_data.xlsx', engine='openpyxl')

    for _, row in df.iterrows():
        # Make sure the customer exists before creating the loan
        if Customer.objects.filter(customer_id=row['Customer ID']).exists():
            Loan.objects.update_or_create(
                loan_id=row['Loan ID'],
                defaults={
                    'customer_id': row['Customer ID'],
                    'loan_amount': row['Loan Amount'],
                    'tenure': row['Tenure'],
                    'interest_rate': row['Interest Rate'],
                    'monthly_repayment': row['Monthly payment'],
                    'emis_paid_on_time': row['EMIs paid on Time'],
                    'start_date': row['Date of Approval'],
                    'end_date': row['End Date'],
                }
            )
    return "Loan data ingestion complete."