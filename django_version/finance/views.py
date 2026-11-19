from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Transaction, Budget, PiggyBank
from .forms import TransactionForm, BudgetForm, PiggyBankForm

@login_required
def dashboard_view(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    budgets = Budget.objects.filter(user=request.user)
    piggy_banks = PiggyBank.objects.filter(user=request.user)
    
    trans_form = TransactionForm()
    budget_form = BudgetForm()
    piggy_form = PiggyBankForm()
    
    context = {
        'transactions': transactions,
        'budgets': budgets,
        'piggy_banks': piggy_banks,
        'trans_form': trans_form,
        'budget_form': budget_form,
        'piggy_form': piggy_form,
    }
    return render(request, 'finance/dashboard.html', context)
@login_required
def add_transaction_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
    return redirect('dashboard')
