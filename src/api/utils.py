# src/api/utils.py
from datetime import date
from django.db.models import Sum
from .models import Loan, Customer

def calculate_credit_score(customer_id: int) -> int:
    """
    Calculates a credit score for a given customer based on their loan history.
    - Starts with a baseline score.
    - Penalizes for late payments on past loans.
    - Penalizes for having many active loans.
    - Rewards for paying off loans completely.
    - Fails automatically if total debt exceeds approved limit.
    """
    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return 0 # Customer not found, no score

    customer_loans = Loan.objects.filter(customer=customer)

    # Check for automatic failure condition: sum of current loans > approved limit
    current_debt_sum = customer_loans.filter(end_date__gte=date.today()).aggregate(total=Sum('loan_amount'))['total'] or 0
    if current_debt_sum > customer.approved_limit:
        return 0

    # Start with a baseline score for a good customer
    score = 100

    # 1. Penalize for past late payments
    # This is a simplified model: we penalize if any past loan was not fully paid on time.
    past_loans = customer_loans.filter(end_date__lt=date.today())
    for loan in past_loans:
        if loan.emis_paid_on_time < loan.tenure:
            # Penalize heavily for loans with missed payments
            score -= 25

    # 2. Penalize for high number of current loans
    num_current_loans = customer_loans.filter(end_date__gte=date.today()).count()
    score -= num_current_loans * 10

    # 3. Reward for paying off loans completely
    num_paid_off_loans = past_loans.count()
    score += num_paid_off_loans * 10

    # Ensure score is within the 0-100 range
    final_score = max(0, min(score, 100))

    return final_score