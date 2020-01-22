from django.urls import path
from drfpasswordless.views import (
     ObtainEmailCallbackToken,
     ObtainMobileCallbackToken,
     ObtainAuthTokenFromCallbackToken,
     VerifyAliasFromCallbackToken,
     ObtainEmailVerificationCallbackToken,
     ObtainMobileVerificationCallbackToken,
)

urlpatterns = [
     path('auth/email/', ObtainEmailCallbackToken.as_view(), name='auth_alias'),
     path('auth/mobile/', ObtainMobileCallbackToken.as_view(), name='auth_alias'),
     path('auth/token/', ObtainAuthTokenFromCallbackToken.as_view(), name='auth_callback'),
     path('auth/verify/email/', ObtainEmailVerificationCallbackToken.as_view(), name='verify_email'),
     path('auth/verify/mobile/', ObtainMobileVerificationCallbackToken.as_view(), name='verify_mobile'),
     path('auth/verify/', VerifyAliasFromCallbackToken.as_view(), name='verify_callback'),
]
