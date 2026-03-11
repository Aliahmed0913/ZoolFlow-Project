import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db(transaction=True)
def test_user_registration_creates_inactive_user_and_cached_code(api_client, mock_mail):
    url = reverse("users:registration")
    payload = {
        "username": "good_father",
        "password": "Strong0913$",
        "email": "example0913@example.com",
    }

    response = api_client.post(path=url, data=payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["email"] == payload["email"]
    assert cache.get(payload["email"]) is not None
    assert mock_mail.called


@pytest.mark.django_db
class TestUserProfileViewSet:
    @pytest.mark.parametrize(
        "role, expected_status",
        [("customer", status.HTTP_403_FORBIDDEN), ("staff", status.HTTP_200_OK)],
    )
    def test_get_profiles(self, api_client, simple_users, role, expected_status):
        api_client.force_authenticate(user=None)
        user = simple_users[role]
        url = reverse("users:user_profile-list")
        api_client.force_authenticate(user=user)
        response = api_client.get(url)
        assert response.status_code == expected_status

    def test_retrieve_update_profile(self, api_client, simple_users):
        api_client.force_authenticate(user=None)
        admin_user = simple_users["admin"]
        customer_user = simple_users["customer"]

        api_client.force_authenticate(user=admin_user)
        detail_url = reverse("users:user_profile-detail", kwargs={"pk": admin_user.id})
        response = api_client.get(detail_url)
        assert response.data["id"] == admin_user.id

        patch_url = reverse("users:user_profile-detail", kwargs={"pk": customer_user.id})
        response = api_client.patch(patch_url, data={"username": "updated_name"})
        customer_user.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert customer_user.username == "updated_name"

    def test_update_get_own_profile(self, api_client, create_user):
        api_client.force_authenticate(user=None)
        user = create_user(username="AliStack", is_active=True)
        url = reverse("users:user_profile-mine")
        api_client.force_authenticate(user=user)

        assert api_client.get(url).status_code == status.HTTP_200_OK
        assert api_client.patch(url, data={"username": "Esteces"}).status_code == status.HTTP_200_OK

    def test_change_password_user(self, api_client, create_user):
        api_client.force_authenticate(user=None)
        user = create_user(is_active=True)
        url = reverse("users:user_profile-new-password")
        api_client.force_authenticate(user=user)
        payload = {"new_password": "Stackpay09$", "old_password": "Aliahmed091$"}
        response = api_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestVerificationCodeViewSet:
    def test_verify_user_code(self, api_client, create_user, verification_code_cache, mocker):
        user = create_user(is_active=False)
        verification_code_cache(user.email, code="246810")
        mocker.patch("zoolflow.users.services.verifying_code.initialize_customer")

        url = reverse("users:verify_code-validate_code")
        payload = {"email": user.email, "code": "246810"}
        response = api_client.post(url, data=payload)

        user.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert user.is_active is True
        assert "access" in response.data

    def test_resend_verify_code(self, api_client, create_user, mock_mail):
        user = create_user(is_active=False)
        cache.delete(user.email)
        url = reverse("users:verify_code-resend_code")

        response = api_client.post(
            url,
            data={
                "email": user.email,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert cache.get(user.email) is not None
        assert mock_mail.called
