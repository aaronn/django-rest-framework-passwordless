from drfpasswordless.settings import api_settings
from django.urls import path
from drfpasswordless.views import (
     ObtainEmailCallbackToken,
     ObtainMobileCallbackToken,
     ObtainAuthTokenFromCallbackToken,
     VerifyAliasFromCallbackToken,
     ObtainEmailVerificationCallbackToken,
     ObtainMobileVerificationCallbackToken,
)

app_name = 'drfpasswordless'

urlpatterns = [
     path(api_settings.PASSWORDLESS_AUTH_PREFIX + 'email/', ObtainEmailCallbackToken.as_view(), name='auth_email'),
     path(api_settings.PASSWORDLESS_AUTH_PREFIX + 'mobile/', ObtainMobileCallbackToken.as_view(), name='auth_mobile'),
     path(api_settings.PASSWORDLESS_AUTH_PREFIX + 'token/', ObtainAuthTokenFromCallbackToken.as_view(), name='auth_token'),
     path(api_settings.PASSWORDLESS_VERIFY_PREFIX + 'email/', ObtainEmailVerificationCallbackToken.as_view(), name='verify_email'),
     path(api_settings.PASSWORDLESS_VERIFY_PREFIX + 'mobile/', ObtainMobileVerificationCallbackToken.as_view(), name='verify_mobile'),
     path(api_settings.PASSWORDLESS_VERIFY_PREFIX, VerifyAliasFromCallbackToken.as_view(), name='verify_token'),
]
