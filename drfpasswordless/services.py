from django.utils.module_loading import import_string
from drfpasswordless.settings import api_settings
from drfpasswordless.utils import (
    create_callback_token_for_user,
    send_email_with_callback_token,
    send_sms_with_callback_token
)


class TokenService(object):
    @staticmethod
    def send_token(user, alias_type, token_type, **message_payload):
        token = create_callback_token_for_user(user, alias_type, token_type)

        send_action = None
        if alias_type == 'email':
            send_action = import_string(api_settings.PASSWORDLESS_AUTH_EMAIL_SEND_FUNCTION)
        elif alias_type == 'mobile':
            send_action = import_string(api_settings.PASSWORDLESS_AUTH_MOBILE_SEND_FUNCTION)
        # Send to alias
        success = send_action(user, token, **message_payload)
        return success
