from django.conf.urls import url
from drfpasswordless.views import ObtainAuthTokenFromCallbackToken, ObtainEmailCallbackToken, ObtainMobileCallbackToken

urlpatterns = [
    url(r'^callback/auth/$', ObtainAuthTokenFromCallbackToken.as_view(), name='auth_callback'),
    url(r'^auth/email/$', ObtainEmailCallbackToken.as_view(), name='auth_email'),
    url(r'^auth/mobile/$', ObtainMobileCallbackToken.as_view(), name='auth_mobile')
]
