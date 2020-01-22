import uuid
from django.db import models
from django.conf import settings
import string
from django.utils.crypto import get_random_string

def generate_hex_token():
    return uuid.uuid1().hex


def generate_numeric_token():
    """
    Generate a random 6 digit string of numbers.
    We use this formatting to allow leading 0s.
    """
    return get_random_string(length=6, allowed_chars=string.digits)


class CallbackTokenManger(models.Manager):
    def active(self):
        return self.get_queryset().filter(is_active=True)

    def inactive(self):
        return self.get_queryset().filter(is_active=False)


class AbstractBaseCallbackToken(models.Model):
    """
    Callback Authentication Tokens
    These tokens present a client with their authorization token
    on successful exchange of a random token (email) or token (for mobile)

    When a new token is created, older ones of the same type are invalidated
    via the pre_save signal in signals.py.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name=None, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    to_alias = models.CharField(blank=True, max_length=254)
    to_alias_type = models.CharField(blank=True, max_length=20)

    objects = CallbackTokenManger()

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ['-id']
        unique_together = (('key', 'is_active'),)

    def __str__(self):
        return str(self.key)


class CallbackToken(AbstractBaseCallbackToken):
    """
    Generates a random six digit number to be returned.
    """
    key = models.CharField(default=generate_numeric_token, max_length=6, unique=True)

    class Meta(AbstractBaseCallbackToken.Meta):
        verbose_name = 'Callback Token'
