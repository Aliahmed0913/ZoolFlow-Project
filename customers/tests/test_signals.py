import pytest
from ..models import Customer, Address, KnowYourCustomer


@pytest.mark.django_db(transaction=True)  # continue here work
def test_customer_startup(create_activate_user, mock_mail):
    # this signal takecare of creating an customer-profile, address, KYC instance.
    # all reference to that customer

    user = create_activate_user()
    customer = Customer.objects.get(user=user)

    assert customer
    assert KnowYourCustomer.objects.filter(customer_id=customer.id).exists()
    assert Address.objects.filter(customer_id=customer.id).exists()

    # ensure that reactivate doesn't lunch new customer
    user.is_active = True
    user.save(update_fields=["is_active"])
    assert Customer.objects.filter(user=user).count() == 1
