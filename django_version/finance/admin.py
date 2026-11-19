from django.contrib import admin
from .models import Category, Transaction, Budget, PiggyBank

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('type',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'amount', 'transaction_type', 'category', 'date')
    list_filter = ('transaction_type', 'date', 'category')
    search_fields = ('title', 'user__username')

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'month')
    list_filter = ('month',)

@admin.register(PiggyBank)
class PiggyBankAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'target_amount', 'current_amount')
