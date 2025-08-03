from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Sum
from datetime import date, timedelta
from django.shortcuts import render
from .models import Customer, Loan
from .utils import calculate_credit_score
from .serializers import (
    CustomerSerializer,
    LoanEligibilityRequestSerializer,
    LoanEligibilityResponseSerializer,
    CreateLoanRequestSerializer,
    CreateLoanResponseSerializer,
    LoanDetailSerializer,
    LoanListSerializer
)

class RegisterAPIView(generics.CreateAPIView):
    """API view to register a new customer."""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        customer = serializer.instance
        
        response_data = {
            'customer_id': customer.customer_id,
            'name': f"{customer.first_name} {customer.last_name}",
            'age': customer.age,
            'monthly_income': customer.monthly_salary,
            'approved_limit': customer.approved_limit,
            'phone_number': customer.phone_number,
        }
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

class CheckEligibilityAPIView(generics.GenericAPIView):
    """API view to check loan eligibility for a customer."""
    def post(self, request, *args, **kwargs):
        serializer = LoanEligibilityRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']

        credit_score = calculate_credit_score(customer_id)
        
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        # --- Definitive Corrected Logic ---
        approval = False
        corrected_interest_rate = None
        final_interest_rate = interest_rate
        
        # Determine the minimum interest rate allowed for the customer's credit score tier
        min_rate_for_tier = None
        can_be_approved = True

        if credit_score > 50:
            min_rate_for_tier = 10.0  # Minimum rate for the best customers
        elif 30 < credit_score <= 50:
            min_rate_for_tier = 12.0
        elif 10 < credit_score <= 30:
            min_rate_for_tier = 16.0
        else: # score < 10
            can_be_approved = False

        if can_be_approved:
            if interest_rate >= min_rate_for_tier:
                approval = True
            else:
                # The loan can be approved, but at the tier's minimum required rate
                approval = True
                corrected_interest_rate = min_rate_for_tier
                final_interest_rate = min_rate_for_tier
        
        # Final check: The 50% EMI rule overrides everything
        current_loans = Loan.objects.filter(customer=customer, end_date__gte=date.today())
        sum_of_emis = current_loans.aggregate(total_emi=Sum('monthly_repayment'))['total_emi'] or 0
        if sum_of_emis > customer.monthly_salary / 2:
            approval = False
            corrected_interest_rate = None # Not applicable if rejected by EMI rule

        # Calculate EMI based on the final interest rate
        monthly_installment = 0
        if approval:
            r = (final_interest_rate / 12) / 100
            n = tenure
            monthly_installment = (loan_amount * r * (1 + r)**n) / ((1 + r)**n - 1) if r > 0 else loan_amount / n

        response_data = {
            'customer_id': customer_id,
            'approval': approval,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': round(monthly_installment, 2)
        }
        
        response_serializer = LoanEligibilityResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class CreateLoanAPIView(generics.GenericAPIView):
    """API view to process and create a new loan."""
    def post(self, request, *args, **kwargs):
        serializer = CreateLoanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']

        credit_score = calculate_credit_score(customer_id)
        customer = Customer.objects.get(pk=customer_id)
        
        # Re-use the exact same logic from eligibility check
        approval = False
        final_interest_rate = interest_rate
        min_rate_for_tier = None
        can_be_approved = True

        if credit_score > 50: min_rate_for_tier = 10.0
        elif 30 < credit_score <= 50: min_rate_for_tier = 12.0
        elif 10 < credit_score <= 30: min_rate_for_tier = 16.0
        else: can_be_approved = False

        if can_be_approved:
            if interest_rate >= min_rate_for_tier:
                approval = True
            else:
                approval = True
                final_interest_rate = min_rate_for_tier

        current_loans = Loan.objects.filter(customer=customer, end_date__gte=date.today())
        sum_of_emis = current_loans.aggregate(total_emi=Sum('monthly_repayment'))['total_emi'] or 0
        if sum_of_emis > customer.monthly_salary / 2:
            approval = False

        # --- Create Loan if Approved ---
        loan_id = None
        monthly_installment = 0
        message = "Loan not approved. Customer does not meet eligibility criteria."

        if approval:
            message = "Loan approved successfully!"
            r = (final_interest_rate / 12) / 100
            n = tenure
            monthly_installment = (loan_amount * r * (1 + r)**n) / ((1 + r)**n - 1) if r > 0 else loan_amount / n

            new_loan = Loan.objects.create(
                customer=customer, loan_amount=loan_amount, tenure=tenure,
                interest_rate=final_interest_rate, monthly_repayment=monthly_installment,
                emis_paid_on_time=0, start_date=date.today(),
                end_date=date.today() + timedelta(days=30 * tenure)
            )
            loan_id = new_loan.loan_id
            
            # Update customer's current debt
            customer.current_debt += loan_amount
            customer.save()

        response_data = {
            'loan_id': loan_id, 'customer_id': customer_id, 'loan_approved': approval,
            'message': message, 'monthly_installment': round(monthly_installment, 2)
        }
        response_serializer = CreateLoanResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class ViewLoanAPIView(generics.RetrieveAPIView):
    """API view to get details of a single loan by its ID."""
    queryset = Loan.objects.all()
    serializer_class = LoanDetailSerializer
    lookup_field = 'loan_id'

class ViewCustomerLoansAPIView(generics.ListAPIView):
    """API view to get a list of all loans for a given customer."""
    serializer_class = LoanListSerializer

    def get_queryset(self):
        customer_id = self.kwargs['customer_id']
        return Loan.objects.filter(customer__customer_id=customer_id)

def frontend_view(request):
    """Serves the frontend HTML file."""
    return render(request, "index.html")