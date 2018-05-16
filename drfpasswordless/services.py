from drfpasswordless.utils import (
    create_callback_token_for_user,
    send_email_with_callback_token,
    send_sms_with_callback_token
)


class TokenService(object):
    @staticmethod
    def send_token(user, alias_type, **message_payload):
        token = create_callback_token_for_user(user, alias_type)
        send_action = None
        if alias_type == 'email':
            send_action = send_email_with_callback_token
        elif alias_type == 'mobile':
            send_action = send_sms_with_callback_token
        # Send to alias
        success = send_action(user, token, **message_payload)
        return success
