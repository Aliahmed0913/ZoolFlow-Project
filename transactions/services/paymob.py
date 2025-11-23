from django.core.cache import cache
import requests, logging
import uuid
from customers.models import Address
from stackpay.settings import SUPPORTED_COUNTRIES,CONNECTION_TIMEOUT,PAYMOB_AUTH_CACH_KEY,PAYMOB_API_KEY,AUTH_PAYMOB_TOKEN,ORDER_PAYMOB_URL,PAYMOB_PAYMENT_KEY,PAYMOB_PAYMENT_URL_KEY

logger = logging.getLogger(__name__)

class PayMobServiceError(Exception):
    # Raised when PayMob API fail or return invalid value
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details
    
class PayMob():
    def __init__(self,customer,address=None,currency=None):
        self.customer = customer
        self.user = self.customer.user
        self.currency = currency
        self.address = address
        
        if not (currency and address):
            self.currency,self.address = self.country_native_currencies()
             
    @staticmethod
    def generate_id():
        '''
        Return an unique ID using uuid 4
        '''
        merchant_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
        logger.info('Merchant ID has successfully created.')
        return merchant_id
    
    def country_native_currencies(self):
        '''
        Return the customer's local currency based on their country and main_address
        '''
        address = Address.objects.filter(customer_id=self.customer.id,main_address=True).first()
        if not address:
            logger.error(f'There is no main address specified for {self.user.username}.')
            raise PayMobServiceError(message='There is no main address specified',details='Address')
        
        currency = SUPPORTED_COUNTRIES.get(address.country.name)
        if not currency:
            logger.error(f'Currency for that country is unsupported.')
            raise PayMobServiceError('Country unsupported',details='Currency')
        
        logger.info('Customer\'s local currency has been successfully determined')
        
        return currency, address
    
    def _request_field(self,payload,endpoint,requested_field,field_name):
        '''
        It's a POST request pattern.
        
        Return the requested field from the endpoint provided 
        '''
        try:
            response = requests.post(url=endpoint, json=payload, timeout=CONNECTION_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            result = data.get(requested_field)
            
            if not result:
                logger.error(f'There is no {field_name} returned when requesting it from PayMob.')
                raise PayMobServiceError(f'The API did not return the {field_name}.',f'{field_name.capitalize()}')
            
            logger.info(f'PayMob {field_name} has successfully returned.')
            return result
        
        except requests.RequestException as pe:
            logger.error(f'Request for PayMob {field_name} fail.')
            raise PayMobServiceError(str(pe),'PayMob API fail')
    

    def get_auth_token(self):
        '''
        Return the authentication token to access the PayMob account using the API key  
        '''
        token = cache.get(PAYMOB_AUTH_CACH_KEY)
        if token:
            logger.info('PayMob authentication token returned.')
            return token
        
        payload = {'api_key':PAYMOB_API_KEY}
        token = self._request_field(payload=payload,endpoint=AUTH_PAYMOB_TOKEN,
                                   requested_field='token',field_name='authentication token')
        
        cache.set(PAYMOB_AUTH_CACH_KEY,token,timeout=60*50)
        
        return token
    
    def _build_order_payload(self,merchant_id,amount_cents):
        token = self.get_auth_token()
        payload = {
            "auth_token": token,
            "delivery_needed": "false",
            "merchant_order_id": merchant_id,
            "amount_cents": amount_cents,  
            "currency": self.currency,
            "items": []
        }
        return payload
    
    def _build_payment_payload(self,amount_cents,paymob_id):
        token = self.get_auth_token()
        payload = {
            'auth_token': token,
            "amount_cents": amount_cents,
            "currency": self.currency,
            "order_id": paymob_id,
            "billing_data":{
                "apartment": self.address.apartment_number,
                "email": self.user.email,
                "first_name": self.customer.first_name,
                "last_name": self.customer.last_name,
                "street": self.address.line,
                "building": self.address.building_number,
                "phone_number":self.customer.phone_number,
                "postal_code": self.address.postal_code,
                "city": self.address.city,
                "country": self.address.country.name,
                "state": self.address.state,
                "floor": "NA",
                "shipping_method": "PKG",
            },
            "integration_id": PAYMOB_PAYMENT_KEY,
        }
        
        return payload
    
    def create_order(self,merchant_id,amount_cents):
        '''
        Create an order in PayMob and return PayMob order ID.
        
        Raises:
            PayMobSerivceError if the API fails or returns no order ID. 
        '''
           
        payload = self._build_order_payload(merchant_id,amount_cents)
        paymob_id = self._request_field(payload=payload,endpoint=ORDER_PAYMOB_URL,requested_field='id',field_name='order ID')
        return paymob_id    
   
    def payment_key_token(self, paymob_id, amount_cents):
        '''
        Return the payment token specialized to who pay. Used to return an iframe 
        '''
     
        payload = self._build_payment_payload(amount_cents,paymob_id)
        payment_token = self._request_field(payload=payload,endpoint=PAYMOB_PAYMENT_URL_KEY,
                                           requested_field='token',field_name='payment token')
        return payment_token
    

        
        