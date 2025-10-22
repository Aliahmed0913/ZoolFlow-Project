from django.contrib import admin
from customers.models import Customer, Address, KnowYourCustomer
from customers.serializers import ADDRESSES_COUNT
# Register your models here.
class AddressInline(admin.TabularInline):
    model = Address
    fields = ('customer','country','line','state','appartment_number','main_address',)
    max_num = ADDRESSES_COUNT

class KYCInline(admin.StackedInline):
    model = KnowYourCustomer
    fields = ('customer','document_type','document_id','document_file','status_tracking','reviewed_at',)
    readonly_fields = ('document_type','document_id','document_file',)
    can_delete = False
    max_num = 1 # Only one KYC per customer
    
@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ('id','first_name','last_name','user__email','is_verified', 'created_at')
    readonly_fields = ('user','is_verified',)
    ordering = ('id',)
    inlines = (KYCInline,AddressInline,)
    
    # Restrict admins from creating new customers or deleting them directly.
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj = ...):
        return False