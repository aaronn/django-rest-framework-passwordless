from rest_framework.authentication import TokenAuthentication
from drfpasswordless.authtoken.models import Token


class TokenAuthentication(TokenAuthentication):
    model = Token