from django.conf.urls import url
from .views import (ObtainEmailCallbackToken,
                    ObtainMobileCallbackToken,
                    ObtainAuthTokenFromCallbackToken,
                    VerifyAliasFromCallbackToken,
                    ObtainEmailVerificationCallbackToken,
                    ObtainMobileVerificationCallbackToken,
                    )

urlpatterns = [url(r'^callback/auth/$', ObtainAuthTokenFromCallbackToken.as_view(), name='auth_callback'),
               url(r'^auth/email/$', ObtainEmailCallbackToken.as_view(), name='auth_email'),
               url(r'^auth/mobile/$', ObtainMobileCallbackToken.as_view(), name='auth_mobile'),
               url(r'^callback/verify/$', VerifyAliasFromCallbackToken.as_view(), name='verify_callback'),
               url(r'^verify/email/$', ObtainEmailVerificationCallbackToken.as_view(), name='verify_email'),
               url(r'^verify/mobile/$', ObtainMobileVerificationCallbackToken.as_view(), name='verify_mobile')]
