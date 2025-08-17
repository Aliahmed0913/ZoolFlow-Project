from django.contrib.auth.hashers import check_password
from users.serializers import UserSerializer

def check_new_password(view_obj,new_password):
    '''
    Return true if new password is differ from old one after checking that the pattern is met
    '''
    user = view_obj.request.user
    validated_password = UserSerializer.validate_password(view_obj,new_password)
    if not check_password(validated_password,user.password):
        user.set_password(validated_password)
        user.save()
        return True
    return False