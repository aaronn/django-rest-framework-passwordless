![ci-image]

drfpasswordless is a quick way to integrate ‘passwordless’ auth into
your Django Rest Framework project using a user’s email address or
mobile number only (herein referred to as an alias).

Built to work with DRF’s own TokenAuthentication system, it sends the
user a 6-digit callback token to a given email address or a mobile
number. The user sends it back correctly and they’re given an
authentication token (again, provided by Django Rest Framework’s
TokenAuthentication system).

Callback tokens by default expire after 15 minutes.

Example Usage:
==============

```bash
curl -X POST -d “email=aaron@email.com” localhost:8000/auth/email/
```

Email to aaron@email.com:

```
...
<h1>Your login token is 815381.</h1>
...
```

Return Stage

```bash
curl -X POST -d "token=815381" localhost:8000/callback/auth/

> HTTP/1.0 200 OK
> {"token":"76be2d9ecfaf5fa4226d722bzdd8a4fff207ed0e”}
```

Requirements
============

- Python (3.6+)
- Django (2.0+)
- Django Rest Framework + AuthToken (3.6+)
- Python-Twilio (Optional, for mobile.)


Install
=======

1. Install drfpasswordless

   ```
   pipenv install drfpasswordless
   ```

2. Add Django Rest Framework’s Token Authentication to your Django Rest
   Framework project.

```python
 REST_FRAMEWORK = {
     'DEFAULT_AUTHENTICATION_CLASSES':
    ('rest_framework.authentication.TokenAuthentication',
 )}

 INSTALLED_APPS = [
     ...
     'rest_framework',
     'rest_framework.authtoken',
     'drfpasswordless',
      ...
 ]
```

And run
```bash
python manage.py migrate
```

3. Set which types of contact points are allowed for auth in your
   Settings.py. The available options are ``EMAIL`` and ``MOBILE``.

```python
PASSWORDLESS_AUTH = {
   ..
   'PASSWORDLESS_AUTH_TYPES': ['EMAIL', 'MOBILE'],
   ..
}
```

   By default drfpasswordless looks for fields named ``email`` or ``mobile``
   on the User model. If an alias provided doesn’t belong to any given user,
   a new user is created.

   3a. If you’re using ``email``, see the Configuring Email section
   below.

   3b. If you’re using ``mobile``, see the Configuring Mobile section
   below.

4. Add ``drfpasswordless.urls`` to your urls.py

```python
 urlpatterns = [
     ..
     path('', include('drfpasswordless.urls')),
     ..
 ]
```

5. You can now POST to either of the endpoints:

```bash
curl -X POST -d "email=aaron@email.com" localhost:8000/auth/email/

// OR

curl -X POST -d "mobile=+15552143912" localhost:8000/auth/mobile/
```
   A 6 digit callback token will be sent to the contact point.

6. The client has 15 minutes to use the 6 digit callback token
   correctly. If successful, they get an authorization token in exchange
   which the client can then use with Django Rest Framework’s
   TokenAuthentication scheme.

```bash
curl -X POST -d "token=815381" localhost:8000/callback/auth/

> HTTP/1.0 200 OK
> {"token":"76be2d9ecfaf5fa4226d722bzdd8a4fff207ed0e”}
```

Configuring Emails
------------------

Specify the email address you’d like to send the callback token from
with the ``PASSWORDLESS_EMAIL_NOREPLY_ADDRESS`` setting.
```python
PASSWORDLESS_AUTH = {
   ..
   'PASSWORDLESS_AUTH_TYPES': ['EMAIL',],
   'PASSWORDLESS_EMAIL_NOREPLY_ADDRESS': 'noreply@example.com',
   ..
}
```

You’ll also need to set up an SMTP server to send emails (`See Django
Docs <https://docs.djangoproject.com/en/1.10/topics/email/>`__), but for
development you can set up a dummy development smtp server to test
emails. Sent emails will print to the console. `Read more
here. <https://docs.djangoproject.com/en/1.10/topics/email/#configuring-email-for-development>`__

```python
# Settings.py
…
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
```

Then run the following:

```bash
python -m smtpd -n -c DebuggingServer localhost:1025
```

Configuring Mobile
------------------

You’ll need to have the python twilio module installed

```bash
pipenv install twilio
```

and set the ``TWILIO_ACCOUNT_SID`` and ``TWILIO_AUTH_TOKEN`` environment
variables. These are read from `os.environ`, so make sure you don't put
them in your settings file accidentally.

You’ll also need to specify the number you send the token from with the
``PASSWORDLESS_MOBILE_NOREPLY_NUMBER`` setting.

Templates
=========

If you’d like to use a custom email template for your email callback
token, specify your template name with this setting:

```bash
PASSWORDLESS_AUTH = {
   ...
  'PASSWORDLESS_EMAIL_TOKEN_HTML_TEMPLATE_NAME': "mytemplate.html"
}
```

The template renders a single variable ``{{ callback_token }}`` which is
the 6 digit callback token being sent.

Contact Point Validation
========================

Endpoints can automatically mark themselves as validated when a user
logs in with a token sent to a specific endpoint. They can also
automatically mark themselves as invalid when a user changes a contact
point.

This is off by default but can be turned on with
``PASSWORDLESS_USER_MARK_EMAIL_VERIFIED`` or
``PASSWORDLESS_USER_MARK_MOBILE_VERIFIED``. By default when these are
enabled they look for the User model fields ``email_verified`` or
``mobile_verified``.

You can also use ``/validate/email/`` or ``/validate/mobile/`` which will
automatically send a token to the endpoint attached to the current
``request.user``'s email or mobile if available.

You can then send that token to ``/callback/verify/`` which will double-check
that the endpoint belongs to the request.user and mark the alias as verified.

Registration
============

All unrecognized emails and mobile numbers create new accounts by
default. New accounts are automatically set with
``set_unusable_password()`` but it’s recommended that admins have some
type of password.

This can be turned off with the ``PASSWORDLESS_REGISTER_NEW_USERS``
setting.

Other Settings
==============

Here’s a full list of the configurable defaults.

```python
DEFAULTS = {

    # Allowed auth types, can be EMAIL, MOBILE, or both.
    'PASSWORDLESS_AUTH_TYPES': ['EMAIL'],

    # Amount of time that tokens last, in seconds
    'PASSWORDLESS_TOKEN_EXPIRE_TIME': 15 * 60,

    # The user's email field name
    'PASSWORDLESS_USER_EMAIL_FIELD_NAME': 'email',

    # The user's mobile field name
    'PASSWORDLESS_USER_MOBILE_FIELD_NAME': 'mobile',

    # Marks itself as verified the first time a user completes auth via token.
    # Automatically unmarks itself if email is changed.
    'PASSWORDLESS_USER_MARK_EMAIL_VERIFIED': False,
    'PASSWORDLESS_USER_EMAIL_VERIFIED_FIELD_NAME': 'email_verified',

    # Marks itself as verified the first time a user completes auth via token.
    # Automatically unmarks itself if mobile number is changed.
    'PASSWORDLESS_USER_MARK_MOBILE_VERIFIED': False,
    'PASSWORDLESS_USER_MOBILE_VERIFIED_FIELD_NAME': 'mobile_verified',

    # The email the callback token is sent from
    'PASSWORDLESS_EMAIL_NOREPLY_ADDRESS': None,

    # The email subject
    'PASSWORDLESS_EMAIL_SUBJECT': "Your Login Token",

    # A plaintext email message overridden by the html message. Takes one string.
    'PASSWORDLESS_EMAIL_PLAINTEXT_MESSAGE': "Enter this token to sign in: %s",

    # The email template name.
    'PASSWORDLESS_EMAIL_TOKEN_HTML_TEMPLATE_NAME': "passwordless_default_token_email.html",

    # Your twilio number that sends the callback tokens.
    'PASSWORDLESS_MOBILE_NOREPLY_NUMBER': None,

    # The message sent to mobile users logging in. Takes one string.
    'PASSWORDLESS_MOBILE_MESSAGE': "Use this code to log in: %s",

    # Registers previously unseen aliases as new users.
    'PASSWORDLESS_REGISTER_NEW_USERS': True,

    # Suppresses actual SMS for testing
    'PASSWORDLESS_TEST_SUPPRESSION': False,

    # Context Processors for Email Template
    'PASSWORDLESS_CONTEXT_PROCESSORS': [],

    # The verification email subject
    'PASSWORDLESS_EMAIL_VERIFICATION_SUBJECT': "Your Verification Token",

    # A plaintext verification email message overridden by the html message. Takes one string.
    'PASSWORDLESS_EMAIL_VERIFICATION_PLAINTEXT_MESSAGE': "Enter this verification code: %s",

    # The verification email template name.
    'PASSWORDLESS_EMAIL_VERIFICATION_TOKEN_HTML_TEMPLATE_NAME': "passwordless_default_verification_token_email.html",

    # The message sent to mobile users logging in. Takes one string.
    'PASSWORDLESS_MOBILE_VERIFICATION_MESSAGE': "Enter this verification code: %s",

    # Automatically send verification email or sms when a user changes their alias.
    'PASSWORDLESS_AUTO_SEND_VERIFICATION_TOKEN': False,

    # What function is called to construct an authentication tokens when
    # exchanging a passwordless token for a real user auth token. This function
    # should take a user and return a tuple of two values. The first value is
    # the token itself, the second is a boolean value representating whether
    # the token was newly created.
    'PASSWORDLESS_AUTH_TOKEN_CREATOR': 'drfpasswordless.utils.create_authentication_token'
}
```

To Do
----

-  github.io project page
-  Add MkDocs - http://www.mkdocs.org/
-  Support non-US mobile numbers
-  Custom URLs
-  Change bad settings to 500's

Pull requests are encouraged!

Donations & Support
----
If you found drfpasswordless useful, consider giving me a follow
[@aaronykng](https://www.twitter.com/aaronykng) on Twitter and
[@hi.aaron](https://www.instagram.com/hi.aaron) on Instagram.

If you'd like to go a step further and are using drfpasswordless in your startup
or business, consider a donation:

- BTC: `3FzSFeKVABL5Adh9Egoxh77gHbtg2kcTPk`
- ETH: `0x13412a79F06A83B107A8833dB209BECbcb700f24`
- Square Cash: `$aaron`

License
-------

The MIT License (MIT)

Copyright (c) 2018 Aaron Ng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[ci-image]: https://travis-ci.org/aaronn/django-rest-framework-passwordless.svg?branch=master
