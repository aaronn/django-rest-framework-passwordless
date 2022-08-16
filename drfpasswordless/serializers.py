import logging
from functools import reduce
from rest_framework.fields import empty
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from drfpasswordless.models import CallbackToken
from drfpasswordless.settings import api_settings
from landa_exceptions.accounts import InvalidCallbackToken, ExpiredCallbackToken
from drfpasswordless.utils import authenticate_by_token, verify_user_alias, validate_token_age

logger = logging.getLogger(__name__)
User = get_user_model()


class TokenField(serializers.CharField):
    default_error_messages = {
        'required': _('Invalid Token'),
        'invalid': _('Invalid Token'),
        'blank': _('Invalid Token'),
        'max_length': _('Tokens are {max_length} digits long.'),
        'min_length': _('Tokens are {min_length} digits long.')
    }


class AbstractBaseAliasAuthenticationSerializer(serializers.Serializer):
    """
    Abstract class that returns a callback token based on the field given
    Returns a token if valid, None or a message if not.
    """

    @property
    def alias_type(self):
        raise NotImplementedError

    @property
    def alias_attribute_name(self):
        raise NotImplementedError

    def validate(self, attrs):
        alias = attrs.get(self.alias_type)

        if alias:
            # Create or authenticate a user
            # Return THem

            if api_settings.PASSWORDLESS_REGISTER_NEW_USERS is True:
                # If new aliases should register new users.
                user, user_created = User.objects.get_or_create(
                    **{self.alias_attribute_name: alias})

                if user_created:
                    user.set_unusable_password()
                    user.save()
            else:
                # If new aliases should not register new users.
                try:
                    user = User.objects.filter(**{self.alias_attribute_name: alias}).first()
                except User.DoesNotExist:
                    user = None

            if user:
                if not user.is_active:
                    # If valid, return attrs so we can create a token in our logic controller
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)
            else:
                msg = _('No account is associated with this alias.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Missing %s.') % self.alias_type
            raise serializers.ValidationError(msg)

        attrs['user'] = user
        return attrs


class EmailAuthSerializer(AbstractBaseAliasAuthenticationSerializer):
    @property
    def alias_type(self):
        return 'email'

    @property
    def alias_attribute_name(self):
        return api_settings.PASSWORDLESS_EMAIL_ALIAS_ATTRIBUTE_NAME

    email = serializers.EmailField()


class MobileAuthSerializer(AbstractBaseAliasAuthenticationSerializer):
    @property
    def alias_type(self):
        return 'mobile'

    @property
    def alias_attribute_name(self):
        return api_settings.PASSWORDLESS_MOBILE_ALIAS_ATTRIBUTE_NAME

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Mobile number must be entered in the format:"
                                         " '+999999999'. Up to 15 digits allowed.")
    mobile = serializers.CharField(validators=[phone_regex], max_length=15)


"""
Verification
"""


class AbstractBaseAliasVerificationSerializer(serializers.Serializer):
    """
    Abstract class that returns a callback token based on the field given
    Returns a token if valid, None or a message if not.
    """

    @property
    def alias_type(self):
        # The alias type, either email or mobile
        raise NotImplementedError

    def validate(self, attrs):

        msg = _('There was a problem with your request.')

        if self.alias_type:
            # Get request.user
            # Get their specified valid endpoint
            # Validate

            request = self.context["request"]
            if request and hasattr(request, "user"):
                user = request.user
                if user:
                    if not user.is_active:
                        # If valid, return attrs so we can create a token in our logic controller
                        msg = _('User account is disabled.')

                    else:
                        if hasattr(user, self.alias_type):
                            # Has the appropriate alias type
                            attrs['user'] = user
                            return attrs
                        else:
                            msg = _('This user doesn\'t have an %s.' % self.alias_type)
            raise serializers.ValidationError(msg)
        else:
            msg = _('Missing %s.') % self.alias_type
            raise serializers.ValidationError(msg)


class EmailVerificationSerializer(AbstractBaseAliasVerificationSerializer):
    @property
    def alias_type(self):
        return 'email'


class MobileVerificationSerializer(AbstractBaseAliasVerificationSerializer):
    @property
    def alias_type(self):
        return 'mobile'


"""
Callback Token
"""


def token_age_validator(value):
    """
    Check token age
    Makes sure a token is within the proper expiration datetime window.
    """
    valid_token = validate_token_age(value)
    if not valid_token and value != api_settings.DEMO_2FA_PINCODE:
        raise AuthenticationFailed()
    return value


class AbstractBaseCallbackTokenSerializer(serializers.Serializer):
    """
    Abstract class inspired by DRF's own token serializer.
    Returns a user if valid, None or a message if not.
    """
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Mobile number must be entered in the format:"
                                         " '+999999999'. Up to 15 digits allowed.")

    email = serializers.EmailField(required=False)  # Needs to be required=false to require both.
    mobile = serializers.CharField(required=False, validators=[phone_regex], max_length=15)
    token = TokenField(min_length=6, max_length=6, validators=[token_age_validator])

    def validate_alias(self, attrs):
        email = attrs.get('email', None)
        mobile = attrs.get('mobile', None)

        if email and mobile:
            raise serializers.ValidationError()

        if not email and not mobile:
            raise serializers.ValidationError()

        if email:
            return 'email', api_settings.PASSWORDLESS_EMAIL_ALIAS_ATTRIBUTE_NAME, email
        elif mobile:
            return 'mobile', api_settings.PASSWORDLESS_MOBILE_ALIAS_ATTRIBUTE_NAME, mobile

        return None


class CallbackTokenAuthSerializer(AbstractBaseCallbackTokenSerializer):

    def validate(self, attrs, user=None, check_user=True, delete_token=True):
        # Check Aliases
        try:
            alias_type, alias_attribute_name, alias = self.validate_alias(attrs)
            callback_token = attrs.get('token', None)
            if not user and check_user:
                user = User.objects.filter(**{alias_attribute_name: alias}).first()

            tokens = list(
                CallbackToken.objects.filter(
                    user=user,
                    key=callback_token,
                    type=CallbackToken.TOKEN_TYPE_AUTH,
                    to_alias_type=alias_type.upper(),
                    to_alias=attrs.get('mobile', None) or attrs.get('email', None)
                ).all()
            )

            if not tokens:
                msg = _(str(InvalidCallbackToken()))
                raise serializers.ValidationError(msg)

            token = next(filter(lambda _token: _token.is_active, tokens), None)
            if not token:
                raise AuthenticationFailed()

            # Check the token type for our uni-auth method.
            # authenticates and checks the expiry of the callback token.
            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)

                if api_settings.PASSWORDLESS_USER_MARK_EMAIL_VERIFIED \
                        or api_settings.PASSWORDLESS_USER_MARK_MOBILE_VERIFIED:
                    # Mark this alias as verified
                    user = token.user
                    if not user:
                        msg = _(str(InvalidCallbackToken()))
                        raise serializers.ValidationError(msg)

                    success = verify_user_alias(user, token)
                    if success is False:
                        msg = _('Error validating user alias.')
                        raise serializers.ValidationError(msg)

                attrs['user'] = user
                attrs['token'] = token

            if delete_token:
                token.delete()
            return attrs

        except serializers.ValidationError:
            msg = _(str(InvalidCallbackToken()))
            raise serializers.ValidationError(msg)


class CallbackTokenVerificationSerializer(AbstractBaseCallbackTokenSerializer):
    """
    Takes a user and a token, verifies the token belongs to the user and
    validates the alias that the token was sent from.
    """

    def validate(self, attrs):
        try:
            alias_type, alias = self.validate_alias(attrs)
            user_id = self.context.get("user_id")
            user = User.objects.get(**{'id': user_id, alias_type: alias})
            callback_token = attrs.get('token', None)

            token = CallbackToken.objects.get(**{'user': user,
                                                 'key': callback_token,
                                                 'type': CallbackToken.TOKEN_TYPE_VERIFY,
                                                 'is_active': True})

            if token.user == user:
                # Mark this alias as verified
                success = verify_user_alias(user, token)
                if success is False:
                    logger.debug("drfpasswordless: Error verifying alias.")

                attrs['user'] = user
                return attrs
            else:
                msg = _('This token is invalid. Try again later.')
                logger.debug("drfpasswordless: User token mismatch when verifying alias.")

        except CallbackToken.DoesNotExist:
            msg = _('We could not verify this alias.')
            logger.debug("drfpasswordless: Tried to validate alias with bad token.")
            pass
        except User.DoesNotExist:
            msg = _('We could not verify this alias.')
            logger.debug("drfpasswordless: Tried to validate alias with bad user.")
            pass
        except PermissionDenied:
            msg = _('Insufficient permissions.')
            logger.debug("drfpasswordless: Permission denied while validating alias.")
            pass

        raise serializers.ValidationError(msg)


"""
Responses
"""


class TokenResponseSerializer(serializers.Serializer):
    """
    Our default response serializer.
    """
    token = serializers.CharField(source='key')
    key = serializers.CharField(write_only=True)


class MagicCallbackTokenAuthSerializer(CallbackTokenAuthSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        if data is not empty:
            data = data['data']['attributes']
            token = CallbackToken.objects.filter(id=data['token']).first()
            if not token:
                raise serializers.ValidationError()
            data['token'] = token.key
        super(MagicCallbackTokenAuthSerializer, self).__init__(instance=instance, data=data, **kwargs)
