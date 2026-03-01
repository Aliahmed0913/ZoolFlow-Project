from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views as v

app_name = "customers"

router = DefaultRouter()
router.register("addresses", v.CustomerAddressViewSet, basename="addresses")

urlpatterns = [
    path("profile", v.CustomerProfileAPIView.as_view(), name="customer_profile"),
    path("", include(router.urls)),
    path(
        "<int:customer_id>/addresses",
        v.CustomerAddressViewSet.as_view(
            {"get": "list", "post": "create", "patch": "partial_update"}
        ),
        name="customer_address",
    ),
    path("kyc", v.KnowYourCustomerListAPIView.as_view(), name="kyc_list"),
    path(
        "kyc/<int:pk>",
        v.KnowYourCustomerStaffDetailAPIView.as_view(),
        name="kyc_staff_detail",
    ),
    path(
        "kyc/me",
        v.KnowYourCustomerDetailAPIView.as_view(),
        name="kyc_customer_detail",
    ),
    path(
        "kyc/<int:pk>/download-doc",
        v.DownloadKnowYourCustomerAPIView.as_view(),
        name="kyc_download",
    ),
]
