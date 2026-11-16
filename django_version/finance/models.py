from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")

    def __str__(self):
        return self.name

class Transaction(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="مبلغ")
    date = models.DateField(verbose_name="تاریخ")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="دسته‌بندی")

    def __str__(self):
        return self.title
