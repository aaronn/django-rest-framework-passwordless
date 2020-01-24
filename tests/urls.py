from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from drfpasswordless.settings import api_settings
from drfpasswordless.views import (ObtainEmailCallbackToken,
                                   ObtainMobileCallbackToken,
                                   ObtainAuthTokenFromCallbackToken,
                                   VerifyAliasFromCallbackToken,
                                   ObtainEmailVerificationCallbackToken,
                                   ObtainMobileVerificationCallbackToken, )

app_name = 'drfpasswordless'

urlpatterns = [
    path('', include('drfpasswordless.urls')),
]

format_suffix_patterns(urlpatterns)
