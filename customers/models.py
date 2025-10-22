from django.db import models
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField
from customers.validators import validate_phone, valid_age, validate_customer_name 
from rest_framework.exceptions import ValidationError
# Create your models here.
User = get_user_model()

class Customer(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='customer_profile')
    
    first_name = models.CharField(max_length=50, null=True, blank=True,validators=[validate_customer_name],
                                help_text='Name must match the name in the document to succeed validation')
    last_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=20,
                                    unique=True,
                                    null=True,blank=True,
                                    validators=[validate_phone])
    dob = models.DateField(null=True,blank=True,validators=[valid_age])
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name or self.user.username
  
class Address(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='addresses')
    country = CountryField(default='EG',editable=False)
    line = models.CharField(max_length=50,blank=True,null=True)
    city = models.CharField(max_length=50,blank=True,null=True)
    state = models.CharField(max_length=50,blank=True,null=True)
    postal_code = models.CharField(max_length=20,blank=True,null=True)
        
    building_nubmer = models.CharField(max_length=10,blank=True,null=True)
    appartment_number = models.CharField(max_length=10,blank=True,null=True)
    main_address = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        super().clean()
        if self.country == 'EG' and not (len(self.postal_code) == 5 and (self.postal_code.isdigit())):
            raise ValidationError({'Postal Code':'In Egypt must be five digits only.'})
    
    def save(self, *arg, **kwargs):
        if self.postal_code:
            self.full_clean()
        super().save(*arg, **kwargs)
    
    def __str__(self):
        return f'{self.customer.full_name or self.customer.user.username} - {self.state}'
    
class KnowYourCustomer(models.Model):
    class DocumentType(models.TextChoices):
        NATIONAL_ID = 'national_id','National_id'
        PASSPORT = 'passport','Passport'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved','Approved'
        REJECTED = 'rejected','Rejected'
    
    customer = models.OneToOneField(Customer,on_delete=models.CASCADE,related_name='kyc')
    document_type = models.CharField(max_length=20,choices=DocumentType.choices,default=DocumentType.NATIONAL_ID)
    document_id = models.CharField(max_length=100,blank=True,null=True)
    document_file = models.FileField(upload_to='kyc-document/')
    status_tracking = models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True,blank=True)
    
    def __str__(self):
        return f'{self.customer.full_name or self.customer.user.username} - {self.document_type}' 
    