from distutils.core import setup

setup(
    name='drfpasswordless',
    version='0.1.0',
    packages=['tests', 'drfpasswordless', 'drfpasswordless.templates'],
    url='https://github.com/aaronn/django-rest-framework-passwordless',
    license='MIT',
    author='Aaron Ng',
    author_email='hi@aaron.ng',
    description='Passwordless auth for Django Rest Framework Token Authentication.'
)

