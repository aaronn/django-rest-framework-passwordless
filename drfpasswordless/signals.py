from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models import signals
from .models import CallbackToken
from .models import generate_numeric_token
from .settings import api_settings


@receiver(signals.pre_save, sender=CallbackToken)
def invalidate_previous_tokens(sender, instance, **kwargs):
    """
    Invalidates all previously issued tokens as a post_save signal.
    """
    active_tokens = None
    if isinstance(instance, CallbackToken):
        active_tokens = CallbackToken.objects.active().filter(user=instance.user).exclude(id=instance.id)

    # Invalidate tokens
    if active_tokens:
        for token in active_tokens:
            token.is_active = False
            token.save()


@receiver(signals.pre_save, sender=CallbackToken)
def check_unique_tokens(sender, instance, **kwargs):
    """
    Ensures that mobile and email tokens are unique or tries once more to generate.
    """
    if isinstance(instance, CallbackToken):
        if CallbackToken.objects.filter(key=instance.key, is_active=True).exists():
            instance.key = generate_numeric_token()


User = get_user_model()


@receiver(signals.pre_save, sender=User)
def update_alias_verification(sender, instance, **kwargs):
    """
    Flags a user's email as unverified if they change it.
    """
    if isinstance(instance, User):

        if instance.id:

            if api_settings.PASSWORDLESS_USER_MARK_EMAIL_VERIFIED is True:
                """
                For marking email aliases as not verified when a user changes it.
                """
                email_field = api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME
                email_verified_field = api_settings.PASSWORDLESS_USER_EMAIL_VERIFIED_FIELD_NAME

                # Verify that this is an existing instance and not a new one.
                try:
                    user_old = User.objects.get(id=instance.id)  # Pre-save object
                    instance_email = getattr(instance, email_field)  # Incoming Email
                    old_email = getattr(user_old, email_field)  # Pre-save object email

                    if instance_email != old_email and instance_email != "":
                        # Email changed, verification should be flagged
                        setattr(instance, email_verified_field, False)

                except User.DoesNotExist:
                    # User probably is just initially being created
                    setattr(instance, email_verified_field, True)

            if api_settings.PASSWORDLESS_USER_MARK_MOBILE_VERIFIED is True:
                """
                For marking mobile aliases as not verified when a user changes it.
                """
                mobile_field = api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME
                mobile_verified_field = api_settings.PASSWORDLESS_USER_MOBILE_VERIFIED_FIELD_NAME

                # Verify that this is an existing instance and not a new one.
                try:
                    user_old = User.objects.get(id=instance.id)  # Pre-save object
                    instance_mobile = getattr(instance, mobile_field)  # Incoming mobile
                    old_mobile = getattr(user_old, mobile_field)  # Pre-save object mobile

                    if instance_mobile != old_mobile and instance_mobile != "":
                        # Mobile changed, verification should be flagged
                        setattr(instance, mobile_verified_field, False)

                except User.DoesNotExist:
                    # User probably is just initially being created
                    setattr(instance, mobile_verified_field, True)
