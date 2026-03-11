import logging
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .pagination import TransactionPagination
from .serializers import TransactionSerializer
from .models import Transaction
from .permissions import IsVerifiedCustomer
from .services.orchestration import (
    TransactionOrchestrationService,
    TransactionOrchestrationServiceError,
)
from .services.webhook import WebhookServiceError, WebhookService
from .services.paymob import ProviderServiceError

user = get_user_model()
logger = logging.getLogger(__name__)


def _request_context(request):
    return {
        "request_id": request.headers.get("X-Request-ID", ""),
        "path": request.path,
    }


# Create your views here.
class TransactionViewSet(ModelViewSet):
    http_method_names = ["get", "post"]
    permission_classes = [IsAuthenticated, IsVerifiedCustomer]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["state", "created_at"]

    def get_queryset(self):
        """filter transactions based on user role"""
        role = self.request.user.role_management
        if role == user.Roles.CUSTOMER:
            return Transaction.objects.filter(customer__user=self.request.user)
        # permission for staff to view all transactions only
        elif role in (user.Roles.STAFF, user.Roles.ADMIN):
            return Transaction.objects.all()
        return Transaction.objects.none()

    def create(self, request, *args, **kwargs):
        """
        Create a new transaction with PayMob orchestration.
        CSRF protection for browser clients.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = request.user.customer_profile
        validated_data = dict(serializer.validated_data)
        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key and len(idempotency_key) > 64:
            return Response(
                {"non_field_errors": ["Idempotency-Key exceeds max length (64)."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if idempotency_key:
            existing = Transaction.objects.filter(
                customer=customer,
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                logger.info(
                    "Idempotent transaction replay served.",
                    extra={"transaction_id": existing.id, **_request_context(request)},
                )
                output_serializer = self.get_serializer(existing)
                return Response(output_serializer.data, status=status.HTTP_200_OK)
            validated_data["idempotency_key"] = idempotency_key

        try:
            orchestration_service = TransactionOrchestrationService(customer)
            transaction = orchestration_service.create_transaction(
                validated_data,
            )
        except IntegrityError:
            if idempotency_key:
                existing = Transaction.objects.filter(
                    customer=customer,
                    idempotency_key=idempotency_key,
                ).first()
                if existing:
                    output_serializer = self.get_serializer(existing)
                    return Response(output_serializer.data, status=status.HTTP_200_OK)
            raise
        except TransactionOrchestrationServiceError as e:
            return Response(
                {"non_field_errors": [f"{e.details}:{e.message}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Transaction created successfully.",
            extra={
                "merchant_order_id": transaction.merchant_order_id,
                "customer_id": customer.id,
                **_request_context(request),
            },
        )
        output_serializer = self.get_serializer(transaction)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PayMobWebHookView(APIView):
    def post(self, request):
        try:
            data = request.data.get("obj")
            if not data or not isinstance(data, dict):
                return Response(
                    {"Webhook": "Invalid webhook payload."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transaction_id = data.get("id")
            merchant_id = data.get("order", {}).get("merchant_order_id")
            if not transaction_id or not merchant_id:
                return Response(
                    {"Webhook": "Missing transaction reference fields."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check incoming HMAC signature with computed one internally
            w_service = WebhookService(data, merchant_id, transaction_id)
            received_hmac = request.GET.get("hmac")
            w_service.verify_paymob_hmac(received_hmac)

            # Update transaction and mail this updates
            TransactionOrchestrationService.update_and_mail_state(
                merchant_id, transaction_id
            )
            logger.info(
                "Webhook processed successfully.",
                extra={
                    "merchant_order_id": merchant_id,
                    "provider_transaction_id": transaction_id,
                    **_request_context(request),
                },
            )

            return Response(
                {"Webhook": "HMAC successfully verified."},
                status=status.HTTP_200_OK,
            )

        except WebhookServiceError as e:
            return Response(
                {"non_field_errors": [f"{e.details}:{e.message}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ProviderServiceError as e:
            return Response(
                {"non_field_errors": [f"Provider error:{e.message}"]},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except TransactionOrchestrationServiceError as e:
            return Response(
                {"non_field_errors": [f"{e.details}:{e.message}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TransactionView(TemplateView):
    template_name = "zoolflow/transactions/templates/pay.html"
