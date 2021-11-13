from django.urls import path

from drfpasswordless.settings import api_settings
from drfpasswordless.views import (
     ObtainAuthTokenFromCallbackToken
)

app_name = 'drfpasswordless'

urlpatterns = [
    path(api_settings.PASSWORDLESS_AUTH_PREFIX + 'token/', ObtainAuthTokenFromCallbackToken.as_view(),
         name='auth_token'),
]
