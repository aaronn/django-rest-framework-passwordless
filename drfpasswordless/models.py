import uuid
import string
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string

from drfpasswordless.settings import api_settings


def generate_hex_token():
    return uuid.uuid1().hex


def generate_numeric_token():
    """
    Generate a random n-digit string of numbers.
    We use this formatting to allow leading 0s.
    """
    return get_random_string(
        length=api_settings.PASSWORDLESS_CALLBACK_TOKEN_LENGTH,
        allowed_chars=string.digits
    )


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

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name=None,
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    to_alias = models.CharField(blank=True, max_length=254)
    to_alias_type = models.CharField(blank=True, max_length=20)

    objects = CallbackTokenManger()

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
        ordering = ['-id']

    def __str__(self):
        return f'Key: {self.key}'


class CallbackToken(AbstractBaseCallbackToken):
    """
    Generates a random n-digit number to be returned.
    """
    TOKEN_TYPE_AUTH = 'AUTH'
    TOKEN_TYPE_VERIFY = 'VERIFY'
    TOKEN_TYPES = ((TOKEN_TYPE_AUTH, 'Auth'), (TOKEN_TYPE_VERIFY, 'Verify'))

    # key = models.CharField(default=generate_numeric_token, max_length=6)
    key = models.TextField(default=generate_numeric_token)
    type = models.CharField(max_length=20, choices=TOKEN_TYPES)

    def save(self, *args, **kwargs):
        """
        Check length for key.
        """
        if len(self.key) != api_settings.PASSWORDLESS_CALLBACK_TOKEN_LENGTH:
            raise ValueError(
                f'Key length not {api_settings.PASSWORDLESS_CALLBACK_TOKEN_LENGTH}'
            )
        super().save(*args, **kwargs)

    class Meta(AbstractBaseCallbackToken.Meta):
        verbose_name = 'Callback Token'
