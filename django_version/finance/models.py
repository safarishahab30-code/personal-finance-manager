from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    type = models.CharField(max_length=10, choices=[('income', 'درآمد'), ('expense', 'هزینه')], verbose_name="نوع")

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    title = models.CharField(max_length=200, verbose_name="عنوان")
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ (تومان)")
    transaction_type = models.CharField(max_length=10, choices=[('income', 'درآمد'), ('expense', 'هزینه')], verbose_name="نوع")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دسته‌بندی")
    date = models.DateField(verbose_name="تاریخ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    def __str__(self):
        return f"{self.title} - {self.amount} تومان"

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="دسته‌بندی")
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="سقف بودجه (تومان)")
    month = models.CharField(max_length=7, verbose_name="ماه (مثلاً 1405-08)")

    def __str__(self):
        return f"بودجه {self.category.name}: {self.amount}"

class PiggyBank(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    title = models.CharField(max_length=100, verbose_name="عنوان هدف")
    target_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ هدف")
    current_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ پس‌انداز شده")

    def __str__(self):
        return f"قلک: {self.title}"
