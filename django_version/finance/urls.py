from django.urls import path
from finance.views import dashboard_view, add_transaction_view

urlpatterns = [
    path('dashboard/', dashboard_view, name='dashboard'),
    path('transaction/add/', add_transaction_view, name='add_transaction'),
]
