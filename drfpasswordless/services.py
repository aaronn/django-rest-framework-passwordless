import importlib
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
            send_action = send_email_with_callback_token
        elif alias_type == 'mobile':
            sms_action_name = api_settings.PASSWORDLESS_SMS_ACTION.split('.')
            module_name = '.'.join(sms_action_name[:-1])
            try:
                sms_action_module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                send_action = send_sms_with_callback_token
            else:
                send_action = getattr(sms_action_module, sms_action_name[-1])
        # Send to alias
        success = send_action(user, token, **message_payload)
        return success
