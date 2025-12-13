from django.views.generic import TemplateView 
from django_filters.rest_framework import DjangoFilterBackend 
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from transactions.services.webhook import handle_webhook, verify_hmac
from transactions.pagination import TransactionPagination
from transactions.serializers import TransactionSerializer 
from transactions.models import Transaction

user = get_user_model()

# Create your views here.
@method_decorator(csrf_protect,name='post')
class TransactionAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status','created_at']
    
    def get_queryset(self):
        role = self.request.user.role_management
        if role == user.Roles.CUSTOMER:
            return Transaction.objects.filter(customer=self.request.user.customer_profile)
    
        return Transaction.objects.all()

class PayMobWebHookView(APIView):
    def post(self,request):
        received_hmac = request.GET.get('hmac')
        data = request.data.get('obj') 
        merchant_id = data.get('order',{}).get('merchant_order_id')
        success = data.get('success')
        is_verified = verify_hmac(received_hmac,data)
        
        if merchant_id and is_verified:
            # updating the status of transaction 
            handle_webhook(merchant_id,success)
            return Response({'Received':True},status=status.HTTP_200_OK)
        
        return Response({'Received':False},status=status.HTTP_400_BAD_REQUEST)

class TransactionView(TemplateView):
    template_name ='transactions/templates/pay.html'
    
    
 