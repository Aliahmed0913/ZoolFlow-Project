from django.db import models
from customers.models import Customer
from django.core.validators import MinValueValidator
from decimal import Decimal
# Create your models here.

class Transaction(models.Model):
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending','Pending'
        SUCCESS = 'success','Success'
        FAILED = 'failed','Failed'
        
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_transaction')
    amount = models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=10,choices=TransactionStatus.choices,default=TransactionStatus.PENDING)
    merchant_order_id = models.CharField(max_length=200,unique=True)
    paymob_order_id = models.CharField(max_length=200,null=True,blank=True)
    paymob_payment_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transaction {self.merchant_order_id} ({self.status})"

    class Meta:
        ordering = ['-created_at']