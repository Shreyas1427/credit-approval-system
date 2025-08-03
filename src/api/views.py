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
        customer = Customer.objects.get(pk=customer_id)
        
        current_loans = Loan.objects.filter(customer=customer, end_date__gte=date.today())
        sum_of_emis = current_loans.aggregate(total_emi=Sum('monthly_repayment'))['total_emi'] or 0

        approval = False
        corrected_interest_rate = None

        if sum_of_emis > customer.monthly_salary / 2:
            approval = False
        else:
            if credit_score > 50:
                approval = True
            elif 30 < credit_score <= 50:
                if interest_rate > 12:
                    approval = True
                else:
                    corrected_interest_rate = 12.0
            elif 10 < credit_score <= 30:
                if interest_rate > 16:
                    approval = True
                else:
                    corrected_interest_rate = 16.0

        final_interest_rate = corrected_interest_rate if corrected_interest_rate is not None else interest_rate
        if corrected_interest_rate is not None and not approval:
            final_interest_rate = corrected_interest_rate
            approval = True

        r = (final_interest_rate / 12) / 100
        n = tenure
        monthly_installment = (loan_amount * r * (1 + r)**n) / ((1 + r)**n - 1) if r > 0 else loan_amount / n

        response_data = {
            'customer_id': customer_id, 'approval': approval, 'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_interest_rate, 'tenure': tenure,
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
        
        current_loans = Loan.objects.filter(customer=customer, end_date__gte=date.today())
        sum_of_emis = current_loans.aggregate(total_emi=Sum('monthly_repayment'))['total_emi'] or 0

        approval = False
        message = "Loan not approved due to low credit score or high existing debt."
        
        if sum_of_emis <= customer.monthly_salary / 2:
            if credit_score > 50:
                approval = True
            elif 30 < credit_score <= 50 and interest_rate > 12:
                approval = True
            elif 10 < credit_score <= 30 and interest_rate > 16:
                approval = True

        final_interest_rate = interest_rate
        if not approval:
            if 30 < credit_score <= 50:
                final_interest_rate = 12.0
            elif 10 < credit_score <= 30:
                final_interest_rate = 16.0
            
            if final_interest_rate != interest_rate:
                 message = "Loan not approved at requested interest rate. Can be approved at a higher rate."
                 approval = False # Keep approval false, but indicate a path forward

        loan_id = None
        monthly_installment = 0
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