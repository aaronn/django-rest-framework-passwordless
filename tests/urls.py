from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from drfpasswordless.views import (ObtainEmailCallbackToken,
                                   ObtainMobileCallbackToken,
                                   ObtainAuthTokenFromCallbackToken,
                                   VerifyAliasFromCallbackToken,
                                   ObtainEmailVerificationCallbackToken,
                                   ObtainMobileVerificationCallbackToken, )

urlpatterns = [url(r'^auth/token/$', ObtainAuthTokenFromCallbackToken.as_view(), name='auth_callback'),
               url(r'^auth/email/$', ObtainEmailCallbackToken.as_view(), name='auth_email'),
               url(r'^auth/mobile/$', ObtainMobileCallbackToken.as_view(), name='auth_mobile'),
               url(r'^auth/verify/$', VerifyAliasFromCallbackToken.as_view(), name='verify_callback'),
               url(r'^auth/verify/email/$', ObtainEmailVerificationCallbackToken.as_view(), name='verify_email'),
               url(r'^auth/verify/mobile/$', ObtainMobileVerificationCallbackToken.as_view(), name='verify_mobile')]

format_suffix_patterns(urlpatterns)
