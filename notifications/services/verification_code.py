from notifications.tasks import mail_code_task

def send_verification_code(code_id):
    '''
    Only interface for sending verification user code in email 
    this is entrypoint used by another app
    '''
    mail_code_task.delay(code_id)
    
    
