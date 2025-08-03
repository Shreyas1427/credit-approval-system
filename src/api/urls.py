from django.urls import path
from .views import RegisterAPIView
from .views import CheckEligibilityAPIView 
from .views import CreateLoanAPIView 
from .views import ViewLoanAPIView, ViewCustomerLoansAPIView 



urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('check-eligibility/', CheckEligibilityAPIView.as_view(), name='check-eligibility'),
    path('create-loan/', CreateLoanAPIView.as_view(), name='create-loan'),
    path('view-loan/<int:loan_id>/', ViewLoanAPIView.as_view(), name='view-loan'),
    path('view-loans/<int:customer_id>/', ViewCustomerLoansAPIView.as_view(), name='view-customer-loans'),
]