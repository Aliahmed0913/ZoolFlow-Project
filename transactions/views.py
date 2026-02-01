import logging
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
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
from .services.helpers import bring_transaction
from .services.webhook import WebhookServiceError, WebhookService

user = get_user_model()
logger = logging.getLogger(__name__)


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
            return bring_transaction(
                customer=self.request.user.customer_profile,
            )
        return Transaction.objects.all()

    @method_decorator(csrf_protect)
    def create(self, request, *args, **kwargs):
        """
        Create a new transaction with PayMob orchestration.
        CSRF protection for browser clients.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = request.user.customer_profile
        validated_data = serializer.validated_data

        try:
            orchestration_service = TransactionOrchestrationService(customer)
            transaction = orchestration_service.create_transaction(
                validated_data,
            )
        except TransactionOrchestrationServiceError as e:
            return Response(
                {"non_field_errors": [f"{e.details}:{e.message}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output_serializer = self.get_serializer(transaction)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PayMobWebHookView(APIView):
    def post(self, request):
        try:
            data = request.data.get("obj")
            if not data:
                return Response(
                    {"Webhook": "Invalid webhook data received."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # check idempotency based on transaction id
            transaction_id = data.get("id")
            transaction = bring_transaction(transaction_id=transaction_id)

            if transaction:
                # check if transaction is already processed
                if transaction.state != transaction.TransactionState.PENDING:
                    logger.warning(
                        f"Transaction {transaction_id} already processed",
                    )
                    return Response(
                        {"Webhook": "Transaction already processed."},
                        status=status.HTTP_200_OK,
                    )

            # Check incoming HMAC signature with computed one internally
            w_service = WebhookService(data, transaction_id)
            received_hmac = request.GET.get("hmac")
            w_service.verify_paymob_hmac(received_hmac)

            # Process webhook data to update transaction state
            w_service.handle_webhook()

            return Response(
                {"Webhook": "HMAC successfully verified."},
                status=status.HTTP_200_OK,
            )

        except WebhookServiceError as e:
            return Response(
                {"non_field_errors": [f"{e.details}:{e.message}"]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TransactionView(TemplateView):
    template_name = "transactions/templates/pay.html"
