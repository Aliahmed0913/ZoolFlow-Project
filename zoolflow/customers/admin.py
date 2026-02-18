from django.contrib import admin
from zoolflow.customers.models import Customer, Address, KnowYourCustomer
from config.settings import ADDRESSES_COUNT
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError


# Register your models here.
class AddressInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # forms that are not deleted and have data
        active = [
            f
            for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get("DELETE", False)
        ]

        # max 3 addresses
        if len(active) > ADDRESSES_COUNT:
            raise ValidationError("Allowed only 3 addresses.")

        # must have exactly one main address
        mains = [f for f in active if f.cleaned_data.get("main_address")]

        if len(mains) == 0:
            raise ValidationError("Must be at least one main address.")
        if len(mains) > 1:
            raise ValidationError("Only one main address is allowed.")


class AddressInline(admin.StackedInline):
    model = Address
    formset = AddressInlineFormSet
    fields = (
        "line",
        "state",
        "apartment_number",
        "postal_code",
        "main_address",
    )
    readonly_fields = ("country",)
    max_num = ADDRESSES_COUNT
    extra = 0


class KYCInline(admin.StackedInline):
    model = KnowYourCustomer
    fields = (
        "document_type",
        "document_id",
        "document_file",
        "status_tracking",
        "reviewed_at",
    )
    readonly_fields = (
        "document_type",
        "document_id",
        "document_file",
    )
    can_delete = False
    max_num = 1  # Only one KYC per customer


@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "user__email",
        "is_verified",
        "created_at",
    )
    readonly_fields = (
        "user",
        "is_verified",
    )
    ordering = ("id",)
    inlines = (
        KYCInline,
        AddressInline,
    )

    # Restrict admins from creating new customers or deleting them directly.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=...):
        return False
