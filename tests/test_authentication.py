from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from drfpasswordless.settings import api_settings, DEFAULTS
from drfpasswordless.utils import CallbackToken

User = get_user_model()


class EmailSignUpCallbackTokenTests(APITestCase):

    def setUp(self):
        api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS = 'noreply@example.com'
        self.email_field_name = api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME

        self.url = '/auth/email/'

    def test_email_signup_failed(self):
        email = 'failedemail182+'
        data = {'email': email}

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_signup_success(self):
        email = 'aaron@example.com'
        data = {'email': email}

        # Verify user doesn't exist yet
        user = User.objects.filter(**{self.email_field_name: 'aaron@example.com'}).first()
        # Make sure our user isn't None, meaning the user was created.
        self.assertEqual(user, None)

        # verify a new user was created with serializer
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(**{self.email_field_name: 'aaron@example.com'})
        self.assertNotEqual(user, None)

        # Verify a token exists for the user
        self.assertEqual(CallbackToken.objects.filter(user=user, is_active=True).exists(), 1)

    def test_long_email_signup_success(self):
        # check that application will not fail for emails longer than 40 symbols
        email = '1234567890'*23 + '@example.com'
        data = {'email': email}

        self.assertEqual(len(email), 242)

        # Verify user doesn't exist yet
        user = User.objects.filter(**{self.email_field_name: email}).first()
        # Make sure our user isn't None, meaning the user was created.
        self.assertEqual(user, None)

        # verify a new user was created with serializer
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(**{self.email_field_name: email})
        self.assertNotEqual(user, None)

        callback_token = CallbackToken.objects.filter(user=user, is_active=True).first()
        # Verify a token exists for the user
        self.assertIsNotNone(callback_token)
        self.assertEqual(callback_token.to_alias, email)

    def test_email_signup_disabled(self):
        api_settings.PASSWORDLESS_REGISTER_NEW_USERS = False

        # Verify user doesn't exist yet
        user = User.objects.filter(**{self.email_field_name: 'aaron@example.com'}).first()
        # Make sure our user isn't None, meaning the user was created.
        self.assertEqual(user, None)

        email = 'aaron@example.com'
        data = {'email': email}

        # verify a new user was not created
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(**{self.email_field_name: 'aaron@example.com'}).first()
        self.assertEqual(user, None)

        # Verify no token was created for the user
        self.assertEqual(CallbackToken.objects.filter(user=user, is_active=True).exists(), 0)

    def tearDown(self):
        api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS = DEFAULTS['PASSWORDLESS_EMAIL_NOREPLY_ADDRESS']
        api_settings.PASSWORDLESS_REGISTER_NEW_USERS = DEFAULTS['PASSWORDLESS_REGISTER_NEW_USERS']


class EmailLoginCallbackTokenTests(APITestCase):

    def setUp(self):
        api_settings.PASSWORDLESS_AUTH_TYPES = ['EMAIL']
        api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS = 'noreply@example.com'

        self.email = 'aaron@example.com'
        self.url = '/auth/email/'
        self.challenge_url = '/callback/auth/'

        self.email_field_name = api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME
        self.user = User.objects.create(**{self.email_field_name: self.email})

    def test_email_auth_failed(self):
        data = {'email': self.email}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token sent to alias
        challenge_data = {'token': '123456'}  # Send an arbitrary token instead

        # Try to auth with the callback token
        challenge_response = self.client.post(self.challenge_url, challenge_data)
        self.assertEqual(challenge_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_auth_expired(self):
        data = {'email': self.email}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token sent to alias
        callback_token = CallbackToken.objects.filter(user=self.user, is_active=True).first()
        challenge_data = {'token': callback_token}

        data = {'email': self.email}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Second token sent to alias
        second_callback_token = CallbackToken.objects.filter(user=self.user, is_active=True).first()
        second_challenge_data = {'token': second_callback_token}

        # Try to auth with the old callback token
        challenge_response = self.client.post(self.challenge_url, challenge_data)
        self.assertEqual(challenge_response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try to auth with the new callback token
        second_challenge_response = self.client.post(self.challenge_url, second_challenge_data)
        self.assertEqual(second_challenge_response.status_code, status.HTTP_200_OK)

        # Verify Auth Token
        auth_token = second_challenge_response.data['token']
        self.assertEqual(auth_token, Token.objects.filter(key=auth_token).first().key)

    def test_email_auth_success(self):
        data = {'email': self.email}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token sent to alias
        callback_token = CallbackToken.objects.filter(user=self.user, is_active=True).first()
        challenge_data = {'token': callback_token}

        # Try to auth with the callback token
        challenge_response = self.client.post(self.challenge_url, challenge_data)
        self.assertEqual(challenge_response.status_code, status.HTTP_200_OK)

        # Verify Auth Token
        auth_token = challenge_response.data['token']
        self.assertEqual(auth_token, Token.objects.filter(key=auth_token).first().key)

    def tearDown(self):
        api_settings.PASSWORDLESS_AUTH_TYPES = DEFAULTS['PASSWORDLESS_AUTH_TYPES']
        api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS = DEFAULTS['PASSWORDLESS_EMAIL_NOREPLY_ADDRESS']
        self.user.delete()


"""
Mobile Tests
"""


class MobileSignUpCallbackTokenTests(APITestCase):

    def setUp(self):
        api_settings.PASSWORDLESS_TEST_SUPPRESSION = True
        api_settings.PASSWORDLESS_AUTH_TYPES = ['MOBILE']
        api_settings.PASSWORDLESS_MOBILE_NOREPLY_NUMBER = '+15550000000'
        self.url = '/auth/mobile/'

        self.mobile_field_name = api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME

    def test_mobile_signup_failed(self):
        mobile = 'sidfj98zfd'
        data = {'mobile': mobile}

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_signup_success(self):
        mobile = '+15551234567'
        data = {'mobile': mobile}

        # Verify user doesn't exist yet
        user = User.objects.filter(**{self.mobile_field_name: '+15551234567'}).first()
        # Make sure our user isn't None, meaning the user was created.
        self.assertEqual(user, None)

        # verify a new user was created with serializer
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(**{self.mobile_field_name: '+15551234567'})
        self.assertNotEqual(user, None)

        # Verify a token exists for the user
        self.assertEqual(CallbackToken.objects.filter(user=user, is_active=True).exists(), 1)

    def test_mobile_signup_disabled(self):
        api_settings.PASSWORDLESS_REGISTER_NEW_USERS = False

        # Verify user doesn't exist yet
        user = User.objects.filter(**{self.mobile_field_name: '+15557654321'}).first()
        # Make sure our user isn't None, meaning the user was created.
        self.assertEqual(user, None)

        mobile = '+15557654321'
        data = {'mobile': mobile}

        # verify a new user was not created
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(**{self.mobile_field_name: '+15557654321'}).first()
        self.assertEqual(user, None)

        # Verify no token was created for the user
        self.assertEqual(CallbackToken.objects.filter(user=user, is_active=True).exists(), 0)

    def tearDown(self):
        api_settings.PASSWORDLESS_TEST_SUPPRESSION = DEFAULTS['PASSWORDLESS_TEST_SUPPRESSION']
        api_settings.PASSWORDLESS_AUTH_TYPES = DEFAULTS['PASSWORDLESS_AUTH_TYPES']
        api_settings.PASSWORDLESS_REGISTER_NEW_USERS = DEFAULTS['PASSWORDLESS_REGISTER_NEW_USERS']
        api_settings.PASSWORDLESS_MOBILE_NOREPLY_NUMBER = DEFAULTS['PASSWORDLESS_MOBILE_NOREPLY_NUMBER']


class MobileLoginCallbackTokenTests(APITestCase):

    def setUp(self):
        api_settings.PASSWORDLESS_TEST_SUPPRESSION = True
        api_settings.PASSWORDLESS_AUTH_TYPES = ['MOBILE']
        api_settings.PASSWORDLESS_MOBILE_NOREPLY_NUMBER = '+15550000000'

        self.mobile = '+15551234567'
        self.url = '/auth/mobile/'
        self.challenge_url = '/callback/auth/'

        self.mobile_field_name = api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME

        self.user = User.objects.create(**{self.mobile_field_name: self.mobile})

    def test_mobile_auth_failed(self):
        data = {'mobile': self.mobile}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token sent to alias
        challenge_data = {'token': '123456'}  # Send an arbitrary token instead

        # Try to auth with the callback token
        challenge_response = self.client.post(self.challenge_url, challenge_data)
        self.assertEqual(challenge_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_auth_expired(self):
        data = {'mobile': self.mobile}
        first_response = self.client.post(self.url, data)
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        # Token sent to alias
        first_callback_token = CallbackToken.objects.filter(user=self.user, is_active=True).first()
        first_challenge_data = {'token': first_callback_token}

        data = {'mobile': self.mobile}
        second_response = self.client.post(self.url, data)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)

        # Second token sent to alias
        second_callback_token = CallbackToken.objects.filter(user=self.user, is_active=True).first()
        second_challenge_data = {'token': second_callback_token}

        # Try to auth with the old callback token
        challenge_response = self.client.post(self.challenge_url, first_challenge_data)
        self.assertEqual(challenge_response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try to auth with the new callback token
        second_challenge_response = self.client.post(self.challenge_url, second_challenge_data)
        self.assertEqual(second_challenge_response.status_code, status.HTTP_200_OK)

        # Verify Auth Token
        auth_token = second_challenge_response.data['token']
        self.assertEqual(auth_token, Token.objects.filter(key=auth_token).first().key)

    def test_mobile_auth_success(self):
        data = {'mobile': self.mobile}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token sent to alias
        callback_token = CallbackToken.objects.filter(user=self.user, is_active=True).first()
        challenge_data = {'token': callback_token}

        # Try to auth with the callback token
        challenge_response = self.client.post(self.challenge_url, challenge_data)
        self.assertEqual(challenge_response.status_code, status.HTTP_200_OK)

        # Verify Auth Token
        auth_token = challenge_response.data['token']
        self.assertEqual(auth_token, Token.objects.filter(key=auth_token).first().key)

    def tearDown(self):
        api_settings.PASSWORDLESS_TEST_SUPPRESSION = DEFAULTS['PASSWORDLESS_TEST_SUPPRESSION']
        api_settings.PASSWORDLESS_AUTH_TYPES = DEFAULTS['PASSWORDLESS_AUTH_TYPES']
        api_settings.PASSWORDLESS_MOBILE_NOREPLY_NUMBER = DEFAULTS['PASSWORDLESS_MOBILE_NOREPLY_NUMBER']
        self.user.delete()
