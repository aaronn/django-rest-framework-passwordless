from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import ObtainEmailCallbackToken, ObtainMobileCallbackToken, ObtainAuthTokenFromCallbackToken

urlpatterns = [url(r'^callback/auth/$', ObtainAuthTokenFromCallbackToken.as_view(), name='auth_callback'),
               url(r'^auth/email/$', ObtainEmailCallbackToken.as_view(), name='auth_email'),
               url(r'^auth/mobile/$', ObtainMobileCallbackToken.as_view(), name='auth_mobile')]

format_suffix_patterns(urlpatterns)
