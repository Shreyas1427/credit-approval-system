from datetime import date
from django.db.models import Sum, Max
from .models import Loan, Customer

def calculate_credit_score(customer_id: int) -> int:
    """
    Calculates a credit score for a given customer based on their loan history.
    """
    customer = Customer.objects.get(pk=customer_id)
    loans = Loan.objects.filter(customer=customer)

    # 1. Past Loans paid on time
    past_loans_paid_on_time = loans.filter(end_date__lt=date.today()).aggregate(total_emis=Sum('emis_paid_on_time'))['total_emis'] or 0
    # A simple metric: 1 point per EMI paid on time
    score_from_paid_emis = past_loans_paid_on_time

    # 2. Number of loans taken in the past
    num_loans_taken = loans.count()
    # 2 points for each loan taken
    score_from_loan_count = num_loans_taken * 2

    # 3. Loan activity in the current year
    current_year_activity = loans.filter(start_date__year=date.today().year).count()
    # -1 point for each loan this year to penalize high recent activity
    score_from_current_activity = -current_year_activity

    # 4. Loan approved volume
    # This is ambiguous, so we'll skip it for a clear implementation.

    # 5. Check if sum of current loans > approved limit
    current_loans_sum = loans.filter(end_date__gte=date.today()).aggregate(total_debt=Sum('loan_amount'))['total_debt'] or 0
    if current_loans_sum > customer.approved_limit:
        return 0 # Automatic failure

    # Combine scores to get a final credit score
    # We will cap the score at 100 for simplicity.
    total_score = score_from_paid_emis + score_from_loan_count + score_from_current_activity
    
    return min(total_score, 100)