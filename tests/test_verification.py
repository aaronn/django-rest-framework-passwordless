from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from drfpasswordless.settings import api_settings, DEFAULTS
from drfpasswordless.utils import CallbackToken

User = get_user_model()


class AliasEmailVerificationTests(APITestCase):

    def setUp(self):
        api_settings.PASSWORDLESS_AUTH_TYPES = ['EMAIL']
        api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS = 'noreply@example.com'
        api_settings.PASSWORDLESS_USER_MARK_EMAIL_VERIFIED = True

        self.url = reverse('drfpasswordless:auth_email')
        self.callback_url = reverse('drfpasswordless:auth_token')
        self.verify_url = reverse('drfpasswordless:verify_email')
        self.callback_verify = reverse('drfpasswordless:verify_token')
        self.email_field_name = api_settings.PASSWORDLESS_USER_EMAIL_FIELD_NAME
        self.email_verified_field_name = api_settings.PASSWORDLESS_USER_EMAIL_VERIFIED_FIELD_NAME

    def test_email_unverified_to_verified_and_back(self):
        email = 'aaron@example.com'
        email2 = 'aaron2@example.com'
        data = {'email': email}

        # create a new user
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(**{self.email_field_name: email})
        self.assertNotEqual(user, None)
        self.assertEqual(getattr(user, self.email_verified_field_name), False)

        # Verify a token exists for the user, sign in and check verified again
        callback = CallbackToken.objects.filter(user=user, type=CallbackToken.TOKEN_TYPE_AUTH, is_active=True).first()
        callback_data = {'email': email, 'token': callback}
        callback_response = self.client.post(self.callback_url, callback_data)
        self.assertEqual(callback_response.status_code, status.HTTP_200_OK)

        # Verify we got the token, then check and see that email_verified is now verified
        token = callback_response.data['token']
        self.assertEqual(token, Token.objects.get(user=user).key)

        # Refresh and see that the endpoint is now verified as True
        user.refresh_from_db()
        self.assertEqual(getattr(user, self.email_verified_field_name), True)

        # Change email, should result in flag changing to false
        setattr(user, self.email_field_name, email2)
        user.save()
        user.refresh_from_db()
        self.assertEqual(getattr(user, self.email_verified_field_name), False)

        # Verify
        self.client.force_authenticate(user)
        verify_response = self.client.post(self.verify_url)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        # Refresh User
        user = User.objects.get(**{self.email_field_name: email2})
        self.assertNotEqual(user, None)
        self.assertNotEqual(getattr(user, self.email_field_name), None)
        self.assertEqual(getattr(user, self.email_verified_field_name), False)

        # Post callback token back.
        verify_token = CallbackToken.objects.filter(user=user, type=CallbackToken.TOKEN_TYPE_VERIFY, is_active=True).first()
        self.assertNotEqual(verify_token, None)
        verify_callback_response = self.client.post(self.callback_verify, {'email': email2, 'token': verify_token.key})
        self.assertEqual(verify_callback_response.status_code, status.HTTP_200_OK)

        # Refresh User
        user = User.objects.get(**{self.email_field_name: email2})
        self.assertNotEqual(user, None)
        self.assertNotEqual(getattr(user, self.email_field_name), None)
        self.assertEqual(getattr(user, self.email_verified_field_name), True)

    def tearDown(self):
        api_settings.PASSWORDLESS_AUTH_TYPES = DEFAULTS['PASSWORDLESS_AUTH_TYPES']
        api_settings.PASSWORDLESS_EMAIL_NOREPLY_ADDRESS = DEFAULTS['PASSWORDLESS_EMAIL_NOREPLY_ADDRESS']
        api_settings.PASSWORDLESS_USER_MARK_EMAIL_VERIFIED = DEFAULTS['PASSWORDLESS_USER_MARK_MOBILE_VERIFIED']


class AliasMobileVerificationTests(APITestCase):

    def setUp(self):
        api_settings.PASSWORDLESS_TEST_SUPPRESSION = True
        api_settings.PASSWORDLESS_AUTH_TYPES = ['MOBILE']
        api_settings.PASSWORDLESS_MOBILE_NOREPLY_NUMBER = '+15550000000'
        api_settings.PASSWORDLESS_USER_MARK_MOBILE_VERIFIED = True

        self.url = reverse('drfpasswordless:auth_mobile')
        self.callback_url = reverse('drfpasswordless:auth_token')
        self.verify_url = reverse('drfpasswordless:verify_mobile')
        self.callback_verify = reverse('drfpasswordless:verify_token')
        self.mobile_field_name = api_settings.PASSWORDLESS_USER_MOBILE_FIELD_NAME
        self.mobile_verified_field_name = api_settings.PASSWORDLESS_USER_MOBILE_VERIFIED_FIELD_NAME

    def test_mobile_unverified_to_verified_and_back(self):
        mobile = '+15551234567'
        mobile2 = '+15557654321'
        data = {'mobile': mobile}

        # create a new user
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(**{self.mobile_field_name: mobile})
        self.assertNotEqual(user, None)
        self.assertEqual(getattr(user, self.mobile_verified_field_name), False)

        # Verify a token exists for the user, sign in and check verified again
        callback = CallbackToken.objects.filter(user=user, type=CallbackToken.TOKEN_TYPE_AUTH, is_active=True).first()
        callback_data = {'mobile': mobile, 'token': callback}
        callback_response = self.client.post(self.callback_url, callback_data)
        self.assertEqual(callback_response.status_code, status.HTTP_200_OK)

        # Verify we got the token, then check and see that email_verified is now verified
        token = callback_response.data['token']
        self.assertEqual(token, Token.objects.get(user=user).key)

        # Refresh and see that the endpoint is now verified as True
        user.refresh_from_db()
        self.assertEqual(getattr(user, self.mobile_verified_field_name), True)

        # Change mobile, should result in flag changing to false
        setattr(user, self.mobile_field_name, '+15557654321')
        user.save()
        user.refresh_from_db()
        self.assertEqual(getattr(user, self.mobile_verified_field_name), False)

        # Verify
        self.client.force_authenticate(user)
        verify_response = self.client.post(self.verify_url)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)

        # Refresh User
        user = User.objects.get(**{self.mobile_field_name: mobile2})
        self.assertNotEqual(user, None)
        self.assertNotEqual(getattr(user, self.mobile_field_name), None)
        self.assertEqual(getattr(user, self.mobile_verified_field_name), False)

        # Post callback token back.
        verify_token = CallbackToken.objects.filter(user=user, type=CallbackToken.TOKEN_TYPE_VERIFY, is_active=True).first()
        self.assertNotEqual(verify_token, None)
        verify_callback_response = self.client.post(self.callback_verify, {'mobile': mobile2, 'token': verify_token.key})
        self.assertEqual(verify_callback_response.status_code, status.HTTP_200_OK)

        # Refresh User
        user = User.objects.get(**{self.mobile_field_name: mobile2})
        self.assertNotEqual(user, None)
        self.assertNotEqual(getattr(user, self.mobile_field_name), None)
        self.assertEqual(getattr(user, self.mobile_verified_field_name), True)

    def tearDown(self):
        api_settings.PASSWORDLESS_TEST_SUPPRESSION = DEFAULTS['PASSWORDLESS_TEST_SUPPRESSION']
        api_settings.PASSWORDLESS_AUTH_TYPES = DEFAULTS['PASSWORDLESS_AUTH_TYPES']
        api_settings.PASSWORDLESS_MOBILE_NOREPLY_ADDRESS = DEFAULTS['PASSWORDLESS_MOBILE_NOREPLY_NUMBER']
        api_settings.PASSWORDLESS_USER_MARK_MOBILE_VERIFIED = DEFAULTS['PASSWORDLESS_USER_MARK_MOBILE_VERIFIED']
