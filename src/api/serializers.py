
from rest_framework import serializers
from .models import Customer, Loan

class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for registering a new customer."""
    class Meta:
        model = Customer
        # Explicitly list fields for the registration payload
        fields = ['first_name', 'last_name', 'age', 'monthly_salary', 'phone_number']

    def create(self, validated_data):
        # Calculate approved_limit based on monthly_salary
        monthly_salary = validated_data.get('monthly_salary')
        approved_limit = round(36 * monthly_salary / 100000) * 100000
        
        customer = Customer.objects.create(
            **validated_data,
            approved_limit=approved_limit
        )
        return customer

class LoanEligibilityRequestSerializer(serializers.Serializer):
    """Serializer for the incoming /check-eligibility request."""
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class LoanEligibilityResponseSerializer(serializers.Serializer):
    """Serializer for the outgoing /check-eligibility response."""
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField(allow_null=True)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField()

class CreateLoanRequestSerializer(serializers.Serializer):
    """Serializer for the incoming /create-loan request."""
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class CreateLoanResponseSerializer(serializers.Serializer):
    """Serializer for the outgoing /create-loan response."""
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField(allow_null=True)
    monthly_installment = serializers.FloatField()

class CustomerLoanSerializer(serializers.ModelSerializer):
    """A simplified customer serializer for nesting within loan details."""
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone_number', 'age']

class LoanDetailSerializer(serializers.ModelSerializer):
    """Serializer for the /view-loan/<loan_id> endpoint."""
    customer = CustomerLoanSerializer(read_only=True)

    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_repayment', 'tenure', 'customer']

class LoanListSerializer(serializers.ModelSerializer):
    """Serializer for the /view-loans/<customer_id> endpoint."""
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_repayment', 'repayments_left']

    def get_repayments_left(self, obj):
        return obj.tenure - obj.emis_paid_on_time