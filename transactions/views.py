from django.views.generic import TemplateView 
from django_filters.rest_framework import DjangoFilterBackend 
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from transactions.services.transaction_orchestration import create_transaction
from transactions.services.webhook import WebhookServiceError,WebhookService
from transactions.services.paymob import ProviderServiceError
from transactions.pagination import TransactionPagination
from transactions.serializers import TransactionSerializer 
from transactions.models import Transaction
from transactions.permissions import IsVerifiedCustomer

user = get_user_model()

# Create your views here.
class TransactionViewSet(ModelViewSet):
    http_method_names=['get','post']
    permission_classes = [IsAuthenticated, IsVerifiedCustomer]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['state','created_at']
    
    def get_queryset(self):
        '''filter transactions based on user role'''
        role = self.request.user.role_management
        if role == user.Roles.CUSTOMER:
            return Transaction.objects.filter(customer=self.request.user.customer_profile)
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
            transaction = create_transaction(customer, validated_data)
        except ProviderServiceError as e:
            return Response({"non_field_errors": [f'{e.details}:{e.message}']}, status=status.HTTP_400_BAD_REQUEST)
        
        output_serializer = self.get_serializer(transaction)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class PayMobWebHookView(APIView):
    def post(self,request):
        try:
            received_hmac = request.GET.get('hmac')
            data = request.data.get('obj') 
            transaction_id = data.get('id')
            merchant_id = data.get('order',{}).get('merchant_order_id')
            w_service = WebhookService(merchant_id,transaction_id)
        except WebhookServiceError as e:
            return Response({'Webhook':'Miss field/fields or unfound transaction'},status=status.HTTP_400_BAD_REQUEST)
    
        is_verified = w_service.verify_hmac(received_hmac,data)
        if is_verified:
            success = data.get('success')
            pending = data.get('pending')
            is_refunded = data.get('is_refunded')
            
            data_status = data.get('data', {})
            message = data_status.get('message', '')
            response_code = data_status.get('acq_response_code','')   
            w_service.handle_webhook(success,pending,is_refunded,message,response_code)
            return Response({'Webhook':'HMAC successfully verified.'},status=status.HTTP_200_OK)
        
        return Response({'Webhook':'HMAC verification failed.'},status=status.HTTP_400_BAD_REQUEST)

class TransactionView(TemplateView):
    template_name ='transactions/templates/pay.html'
    
    
 