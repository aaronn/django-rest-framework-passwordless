from twilio.rest import Client
import os


def backend(body, to, from_):
    twilio_client = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])

    twilio_client.messages.create(
        body=body,
        to=to,
        from_=from_
    )

    return True
