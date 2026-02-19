import tempfile
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory
from ..models import Address, KnowYourCustomer
from ..permissions import IsCustomer
from ..serializers import CustomerAddressSerializer, CustomerProfileSerializer
from zoolflow.users.models import User


@pytest.mark.django_db()
class TestPermissionsAndSerializers:
    def test_is_customer_permission_allows_customer_and_denies_staff(
        self, create_activate_user
    ):
        customer_user = create_activate_user(
            username="perm_customer",
            email="perm_customer@example.com",
            role_management=User.Roles.CUSTOMER,
        )
        staff_user = create_activate_user(
            username="perm_staff",
            email="perm_staff@example.com",
            role_management=User.Roles.STAFF,
        )

        permission = IsCustomer()
        request_factory = APIRequestFactory()

        customer_request = request_factory.get("/")
        customer_request.user = customer_user
        assert permission.has_permission(customer_request, view=None) is True

        staff_request = request_factory.get("/")
        staff_request.user = staff_user
        assert permission.has_permission(staff_request, view=None) is False

    def test_customer_profile_serializer_is_verified_is_read_only(self):
        serializer = CustomerProfileSerializer(
            data={
                "first_name": "Ali",
                "last_name": "Ahmed",
                "phone_number": "+201012345678",
                "dob": "2000-01-01",
                "is_verified": True,
            }
        )
        assert serializer.is_valid(), serializer.errors
        assert "is_verified" not in serializer.validated_data

    def test_customer_address_serializer_rejects_short_state(
        self, rf, _create_customer
    ):
        user, customer = _create_customer(
            username="short_state",
            email="short_state@example.com",
        )
        request = rf.post("/customers/address/")
        request.user = user

        serializer = CustomerAddressSerializer(
            data={
                "state": "Cai",
                "city": "Cairo",
                "line": "Street",
                "building_number": "10",
                "apartment_number": "2",
                "postal_code": "12345",
                "main_address": False,
                "customer": customer.id,
            },
            context={"request": request},
        )

        assert serializer.is_valid() is False
        assert "state" in serializer.errors


@pytest.mark.django_db()
class TestViews:
    def test_profile_requires_authentication(self, api_client):
        response = api_client.get(reverse("customers:customer-profile"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_denies_non_customer_role(self, api_client, create_activate_user):
        staff = create_activate_user(
            username="staff_profile",
            email="staff_profile@example.com",
            role_management=User.Roles.STAFF,
        )
        api_client.force_authenticate(user=staff)
        response = api_client.get(reverse("customers:customer-profile"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_profile_returns_404_for_customer_without_profile(
        self, api_client, create_activate_user
    ):
        user = create_activate_user(
            username="no_profile",
            email="no_profile@example.com",
            role_management=User.Roles.CUSTOMER,
        )
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse("customers:customer-profile"))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_profile_patch_updates_allowed_fields(self, api_client, _create_customer):
        user, customer = _create_customer(
            username="profile_patch",
            email="profile_patch@example.com",
        )
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse("customers:customer-profile"),
            data={
                "first_name": "Ahmed",
                "last_name": "Ali",
                "phone_number": "+201111111111",
                "dob": "2000-01-01",
                "is_verified": True,
            },
            format="json",
        )
        customer.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert customer.first_name == "Ahmed"
        assert customer.is_verified is False

    def test_address_list_returns_only_authenticated_user_addresses(
        self, api_client, _create_customer
    ):
        user_1, customer_1 = _create_customer(
            username="addr_list_a",
            email="addr_list_a@example.com",
        )
        user_2, customer_2 = _create_customer(
            username="addr_list_b",
            email="addr_list_b@example.com",
        )
        Address.objects.create(
            customer=customer_1,
            state="Cairo",
            city="Cairo",
            line="S1",
            building_number="1",
            apartment_number="1",
            postal_code="12345",
            main_address=False,
        )
        Address.objects.create(
            customer=customer_2,
            state="Giza",
            city="Giza",
            line="S2",
            building_number="2",
            apartment_number="2",
            postal_code="12345",
            main_address=False,
        )

        api_client.force_authenticate(user=user_1)
        response = api_client.get(reverse("customers:addresses-list"))
        own_ids = set(
            Address.objects.filter(customer=customer_1).values_list("id", flat=True)
        )
        returned_ids = {row["id"] for row in response.data}
        assert response.status_code == status.HTTP_200_OK
        assert returned_ids == own_ids

    def test_address_create_respects_max_addresses(self, api_client, _create_customer):
        user, customer = _create_customer(
            username="addr_limit", email="addr_limit@example.com"
        )
        api_client.force_authenticate(user=user)

        payload = {
            "state": "Dakahlia",
            "city": "Mansoura",
            "line": "Main Street",
            "building_number": "14",
            "apartment_number": "33",
            "postal_code": "12345",
            "main_address": False,
        }

        url = reverse("customers:addresses-list")
        second = api_client.post(url, data=payload)
        third = api_client.post(url, data=payload)
        fourth = api_client.post(url, data=payload)

        assert Address.objects.filter(customer=customer).count() == 3
        assert second.status_code == status.HTTP_201_CREATED
        assert third.status_code == status.HTTP_201_CREATED
        assert fourth.status_code == status.HTTP_400_BAD_REQUEST

    def test_address_patch_cannot_remove_only_main_address(
        self, api_client, _create_customer
    ):
        user, customer = _create_customer(
            username="addr_main", email="addr_main@example.com"
        )
        main_address = Address.objects.get(customer=customer, main_address=True)
        api_client.force_authenticate(user=user)
        response = api_client.patch(
            reverse("customers:addresses-detail", args=[main_address.id]),
            data={"main_address": False},
            format="json",
        )
        main_address.refresh_from_db()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert main_address.main_address is True

    @pytest.mark.parametrize(
        "file_name,file_size,content_type,expected",
        [
            ("doc.pdf", 1, "application/pdf", status.HTTP_200_OK),
            ("doc.jpg", 1, "image/jpeg", status.HTTP_200_OK),
            ("doc.svg", 1, "image/svg+xml", status.HTTP_400_BAD_REQUEST),
            ("doc.pdf", 1024 * 251, "application/pdf", status.HTTP_400_BAD_REQUEST),
        ],
    )
    def test_kyc_upload_validates_file_constraints(
        self,
        api_client,
        _create_customer,
        file_name,
        file_size,
        content_type,
        expected,
    ):
        user, _ = _create_customer(
            username=f"kyc_{file_name}_{file_size}",
            email=f"kyc_{file_name}_{file_size}@example.com",
        )
        api_client.force_authenticate(user=user)
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir):
                response = api_client.patch(
                    reverse("customers:kyc-docs"),
                    data={
                        "document_type": KnowYourCustomer.DocumentType.NATIONAL_ID,
                        "document_id": "ABC12345",
                        "document_file": SimpleUploadedFile(
                            file_name,
                            b"f" * file_size,
                            content_type=content_type,
                        ),
                    },
                    format="multipart",
                )
        assert response.status_code == expected
