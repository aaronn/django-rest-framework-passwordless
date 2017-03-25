import logging
import os
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone
from .models import CallbackToken
from .settings import api_settings


log = logging.getLogger(__name__)
User = get_user_model()


def authenticate_by_token(callback_token):
    try:
        token = CallbackToken.objects.get(key=callback_token, is_active=True)

        # Check Token Age
        if validate_token_age(token) is False:
            # If our token is invalid, take away our token.
            token = None

        if token is not None:
            # Our token becomes used now that it's passing through the authentication pipeline.
            token.is_active = False
            token.save()

            if api_settings.PASSWORDLESS_USER_MARK_VERIFIED_EMAIL \
                    or api_settings.PASSWORDLESS_USER_MARK_VERIFIED_MOBILE:
                # Mark this alias as verified
                user = User.objects.get(pk=token.user.pk)
                verify_user_alias(user, token)

            # Returning a user designates a successful authentication.
            return token.user

    except CallbackToken.DoesNotExist:
        pass
    except PermissionDenied:
        pass

    return None


def create_callback_token_for_user(user, token_type):

    token = None
    token_type = token_type.upper()

    if token_type == 'EMAIL':
        token = CallbackToken.objects.create(user=user,
                                             to_alias_type=token_type,
                                             to_alias=getattr(user, api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME))

    elif token_type == 'MOBILE':
        token = CallbackToken.objects.create(user=user,
                                             to_alias_type=token_type,
                                             to_alias=getattr(user, api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME))

    if token is not None:
        return token

    return None


def validate_token_age(token):
    """
    Returns True if a given token is within the age expiration limit.
    """
    seconds = (timezone.now()-token.created_at).total_seconds()
    token_expiry_time = api_settings.PASSWORDLESS_TOKEN_EXPIRE_TIME

    if seconds <= token_expiry_time:
        return True
    else:
        # Invalidate our token.
        token.is_active = False
        token.save()
        return False


def verify_user_alias(user, token):
    """
    Marks a user's contact point as verified depending on accepted token type.
    """
    if token.to_alias_type == 'EMAIL':
        if token.to_alias == getattr(user, api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME):
            setattr(user, api_settings.PASSWORDLESS_USER_EMAIL_VERIFIED_FIELD_NAME, True)
    elif token.to_alias_type == 'MOBILE':
        if token.to_alias == getattr(user, api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME):
            setattr(user, api_settings.PASSWORDLESS_USER_MOBILE_VERIFIED_FIELD_NAME, True)
    else:
        return None
    user.save()
    return user


def send_email_with_callback_token(user, email_token):
    """
    Sends a SMS to user.mobile.

    Passes silently without sending in test environment
    """

    try:
        if api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS:
            html_message = loader.render_to_string(
                api_settings.PASSWORDLESS_EMAIL_TOKEN_HTML_TEMPLATE_NAME,
                {'callback_token': email_token.key, }
            )
            send_mail(
                api_settings.PASSWORDLESS_EMAIL_SUBJECT,
                api_settings.PASSWORDLESS_EMAIL_PLAINTEXT_MESSAGE %
                email_token.key,
                api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS,
                [getattr(user, api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME)],
                fail_silently=False,
                html_message=html_message,
            )
        else:
            log.debug("Failed to send login email. Missing PASSWORDLESS_EMAIL_NOREPLY_ADDRESS.")
            return False
        return True

    except Exception as e:
        log.debug("Failed to send login email to user: %d."
                  "Possibly no email on user object. Email entered was %s" %
                  (user.id, getattr(user, api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME)))
        log.debug(e)
        return False


def send_sms_with_callback_token(user, mobile_token):
    """
    Sends a SMS to user.mobile via Twilio.

    Passes silently without sending in test environment.
    """
    base_string = api_settings.PASSWORDLESS_MOBILE_MESSAGE

    try:
        if hasattr(settings, 'TEST'):
            # If TEST = True in settings, we assume success to prevent spamming SMS during testing.
            if settings.TEST is True:
                return True

        from twilio.rest import TwilioRestClient
        twilio_client = TwilioRestClient(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
        twilio_client.messages.create(
            body=base_string % mobile_token.key,
            to=getattr(user, api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME),
            from_=os.environ['PASSWORDLESS_MOBILE_NOREPLY_NUMBER']
        )
        return True
    except ImportError:
        log.debug("Couldn't import Twilio client. Is twilio installed?")
        return False
    except KeyError:
        log.debug("Couldn't send SMS."
                  "Did you set your Twilio account tokens and specify a PASSWORDLESS_MOBILE_NOREPLY_NUMBER?")
    except Exception as e:
        log.debug("Failed to send login SMS to user: %d. "
                  "Possibly no mobile number on user object or django_twilio isn't set up yet. "
                  "Number entered was %s" % (user.id, getattr(user, api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME)))
        log.debug(e)
        return False
