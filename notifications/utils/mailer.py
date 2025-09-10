from users.models import EmailCode
from django.core.mail import EmailMessage
from stackpay.settings import DEFAULT_FROM_EMAIL
from django.template.loader import render_to_string

def mail_verify_code(user_code:EmailCode):
    '''
    Create and configure EmailMessage instance then send the object
    '''
    subject = 'Verify your email'
    send_to = [user_code.user.email]
    email_from = DEFAULT_FROM_EMAIL
    html_body =  render_to_string('notifications/templates/verification_code.html',{
        'user':user_code.user ,
        'code':user_code.code
    })
    try:
        email = EmailMessage(subject=subject,
                         from_email=email_from,
                         to=send_to,
                         body=html_body)
        email.content_subtype = 'html'
        
        email.send()
    except Exception as error:
        raise 