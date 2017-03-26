from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers
from .settings import api_settings
from .utils import authenticate_by_token


User = get_user_model()

"""
Fields
"""


class TokenField(serializers.CharField):
    default_error_messages = {'required': _('Invalid Token'),
                              'invalid': _('Invalid Token'),
                              'blank': _('Invalid Token'),
                              'max_length': _('Tokens are {max_length} digits long.'),
                              'min_length': _('Tokens are {min_length} digits long.')}


"""
Serializers
"""


class AbstractBaseAliasAuthenticationSerializer(serializers.Serializer):
    """
    Abstract class that returns a callback token based on the field given
    Returns a token if valid, None or a message if not.
    """
    @property
    def alias_type(self):
        # The alias type, either email or mobile
        raise NotImplementedError

    def validate(self, attrs):
        alias = attrs.get(self.alias_type)

        if alias:
            # Create or authenticate a user
            # Return a token for them to log in
            # Consider moving this into somewhere else. Serializer should only serialize.

            if api_settings.PASSWORDLESS_REGISTER_NEW_USERS is True:
                # If new aliases should register new users.
                user, created = User.objects.get_or_create(**{self.alias_type: alias})
            else:
                # If new aliases should not register new users.
                try:
                    user = User.objects.get(**{self.alias_type: alias})
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

    alias_type = 'email'
    email = serializers.EmailField()


class MobileAuthSerializer(AbstractBaseAliasAuthenticationSerializer):

    alias_type = 'mobile'
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Mobile number must be entered in the format:"
                                         " '+999999999'. Up to 15 digits allowed.")
    mobile = serializers.CharField(validators=[phone_regex], max_length=15)


class AbstractBaseCallbackTokenSerializer(serializers.Serializer):
    """
    Abstract class inspired by DRF's own token serializer.
    Returns a user if valid, None or a message if not.
    """

    def validate(self, attrs):
        token = attrs.get('token')

        if token:

            # Check the token type for our uni-auth method.
            # authenticates and checks the expiry of the callback token.
            user = authenticate_by_token(token)
            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)

                attrs['user'] = user
                return attrs

            else:
                msg = _('Invalid Token')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Missing authentication token.')
            raise serializers.ValidationError(msg)


class CallbackTokenSerializer(AbstractBaseCallbackTokenSerializer):
    token = TokenField(min_length=6, max_length=6)
