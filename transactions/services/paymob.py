import requests, logging
from django.core.cache import cache
from django.conf import settings
from transactions.services.http_client import get_session_with_retries
from customers.models import Address

logger = logging.getLogger(__name__)

class ProviderServiceError(Exception):
    # Raised when provider API fail or return invalid value
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details
    
class PayMob():
    def __init__(self,customer,merchant_id,address=None,currency=None):
        self.customer = customer
        self.merchant_id = merchant_id
        self.user = self.customer.user
        self.currency = currency
        self.address = address
        self.session = get_session_with_retries()
        
        if not (currency and address):
            self.currency,self.address = self.country_native_currencies()
    
    def country_native_currencies(self):
        '''
        Return the customer's local currency based on their country and main_address
        '''
        address = Address.objects.filter(customer_id=self.customer.id,main_address=True).first()
        if not address:
            logger.error(f'There is no main address specified for {self.user.username}.')
            raise ProviderServiceError(message='There is no main address specified',details='Address')
        
        currency = getattr(settings,'SUPPORTED_COUNTRIES',{}).get(address.country.name)
        if not currency:
            logger.error(f'Currency for that country is unsupported.')
            raise ProviderServiceError('Country unsupported',details='Currency')
        
        logger.info('Customer\'s local currency has been successfully determined')
        
        return currency, address
    
    def _request_field(self,payload,endpoint,requested_field,field_name):
        '''
        It's a POST request pattern.
        
        Return the requested field from the endpoint provided 
        '''
        try:
            response = self.session.post(url=endpoint, json=payload, timeout=getattr(settings,'CONNECTION_TIMEOUT',(5,5)))
            response.raise_for_status()
            
            data = response.json()
            result = data.get(requested_field)
            
            if not result:
                logger.error(f'No {field_name} returned from provider for transaction {self.merchant_id}.')
                raise ProviderServiceError(f'The API did not return the {field_name}.',f'{field_name.capitalize()}')
            
            logger.info(f'{field_name} for transaction {self.merchant_id} has been successfully returned.')
            return result
        
        except requests.RequestException as pe:
            logger.error(f'transaction {self.merchant_id} failed with error: {str(pe)}')
            raise ProviderServiceError('provider API fail',details=str(pe))
    

    def get_auth_token(self):
        '''
        Return the authentication token to access the provider account using the API key  
        '''
        cache_key = getattr(settings,'PAYMOB_AUTH_CACH_KEY')
        token = cache.get(cache_key)
        if token:
            logger.info('provider authentication token returned.')
            return token
        
        payload = {'api_key':getattr(settings,'PAYMOB_API_KEY')}
        token = self._request_field(payload=payload,endpoint=getattr(settings,'AUTH_PAYMOB_TOKEN'),
                                   requested_field='token',field_name='authentication token')

        cache.set(cache_key,token,timeout=getattr(settings,'CACHE_LIFETIME'))

        return token
    
    def _build_order_payload(self,amount_cents):
        '''
        Set payload for creating an order in provider
        '''
        token = self.get_auth_token()
        payload = {
            "auth_token": token,
            "delivery_needed": "false",
            "merchant_order_id": self.merchant_id,
            "amount_cents": amount_cents,  
            "currency": self.currency,
            "items": []
        }
        return payload
    
    def _build_payment_payload(self,amount_cents,provider_id):
        '''
        Set payload for requesting the payment key token 
        '''
        token = self.get_auth_token()
        payload = {
            'auth_token': token,
            "amount_cents": amount_cents,
            "currency": self.currency,
            "order_id": provider_id,
            "billing_data":{
                "apartment": self.address.apartment_number or 'NA',
                "email": self.user.email or 'Na',
                "first_name": self.customer.first_name or 'NA',
                "last_name": self.customer.last_name or 'un-known',
                "street": self.address.line or 'NA',
                "building": self.address.building_number or 'NA',
                "phone_number":self.customer.phone_number or 'NA',
                "postal_code": self.address.postal_code or 'NA',
                "city": self.address.city or 'NA',
                "country": self.address.country.name or 'NA',
                "state": self.address.state or 'NA',
                "floor": "NA",
                "shipping_method": "PKG",
            },
            "integration_id": getattr(settings,'PAYMOB_PAYMENT_KEY'),
        }
        
        return payload
    
    def create_order(self,amount_cents):
        '''
        Return order ID from provider.
        
        Raises:
            ProviderServiceError if the API fails or returns no order ID. 
        '''
           
        payload = self._build_order_payload(amount_cents)
        provider_id = self._request_field(payload=payload,endpoint=getattr(settings,'ORDER_PAYMOB_URL'),requested_field='id',field_name='order ID')
        return provider_id    
   
    def payment_key_token(self, provider_id, amount_cents):
        '''
        Return the payment token specialized to who pay. Used to return an iframe 
        '''
     
        payload = self._build_payment_payload(amount_cents,provider_id)
        payment_token = self._request_field(payload=payload,endpoint=getattr(settings,'PAYMOB_PAYMENT_URL_KEY'),
                                           requested_field='token',field_name='payment token')
        
        return payment_token