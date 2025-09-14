from django.db import models
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField
# Create your models here.
User = get_user_model()

class Customer(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='customer_profile')
    full_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True,null=True,blank=True)
    country = CountryField(default='EG',editable=False)
    dob = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name or self.user.username
  
class Address(models.Model):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='addresses')
    line = models.CharField(max_length=50,blank=True,null=True)
    state = models.CharField(max_length=20,blank=True,null=True)
    appartment_number = models.CharField(max_length=20,blank=True,null=True)
    main_address = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.customer.full_name or self.customer.user.username} - {self.state}'
    
class KnowYouCustomer(models.Model):
    class DocumentType(models.TextChoices):
        NATIONAL_ID = 'national_id','National_id'
        PASSPORT = 'passport','Passport'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        REVIEW = 'under_review','Under Review'
        APPROVED = 'approved','Approved'
        REJECTED = 'rejected','Rejected'
    
    customer = models.OneToOneField(Customer,on_delete=models.CASCADE,related_name='kyc')
    document_type = models.CharField(max_length=20, choices=DocumentType.choices,default=DocumentType.national)
    document_id = models.CharField(max_length=100,blank=True,null=True)
    document_pic = models.FileField(upload_to='kyc-document/')
    status_tracking = models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True,blank=True)
    
    def __str__(self):
        return f'{self.customer.full_name or self.customer.user.username} - {self.document_type}' 
    