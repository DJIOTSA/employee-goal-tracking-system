from django.contrib.auth.backends import ModelBackend
from .models import Employee, Administrator
from rest_framework.authentication import TokenAuthentication as BaseTokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class EmployeeUserBackend(ModelBackend):
    """ Use to allow proxy user employee to perform authentication """
    def get_user(self, user_id):
        try:
            return Employee.objects.get(pk=user_id)
        except Employee.DoesNotExist:
            return None

class AdministratorUserBackend(ModelBackend):
    """ Use to allow proxy user administrator to perform authentication """
    def get_user(self, user_id):
        try:
            return Administrator.objects.get(pk=user_id)
        except Administrator.DoesNotExist:
            return None

class TokenAuthentication(BaseTokenAuthentication):
    """
    Simple token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = 'Bearer'


class CustomObtainAuthToken(ObtainAuthToken):
    """ 
    Override ObtainAuthToken post function to return additional user 
    information beyond the token value 
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

custom_obtain_auth_token = CustomObtainAuthToken.as_view()

