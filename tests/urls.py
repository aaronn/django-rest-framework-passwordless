from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'drfpasswordless'

urlpatterns = [
    path('', include('drfpasswordless.urls')),
]

format_suffix_patterns(urlpatterns)
