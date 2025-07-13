from email.policy import default
from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)

from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken


def identity_to(instance, filename):
    return 'identity/{filename}'.format(filename=filename)


class UserManager(BaseUserManager):

    def create_user(self, username, firstname, lastname, address, referral_code, phone, email, password=None):
        '''if username is None:
            raise TypeError('Users should have a username')
            '''
        if email is None:
            raise TypeError('Users should have a Email')

        user = self.model(username=username, firstname=firstname, address=address, lastname=lastname,
                          phone=phone, referral_code=referral_code, email=self.normalize_email(email))
        # user = self.model(username=username, #email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

    def create_with_referral_user(self, username, firstname, lastname, address, referral_code, phone, email, password=None):
        '''if username is None:
            raise TypeError('Users should have a username')
            '''
        if email is None:
            raise TypeError('Users should have a Email')

        user = self.model(username=username, firstname=firstname, address=address, lastname=lastname,
                          phone=phone, referral_code=referral_code, email=self.normalize_email(email))
        #user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password=None):
        if password is None:
            raise TypeError('Password should not be none')

        user = self.model(username=username, email=email)
        #user = self.create_user(email, password)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


AUTH_PROVIDERS = {'facebook': 'facebook', 'google': 'google',
                  'twitter': 'twitter', 'email': 'email'}


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        EMPLOYER = 'EMPLOYER', _('Employer')
        JOB_SEEKER = 'JOB_SEEKER', _('Job Seeker')

    username = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    firstname = models.CharField(max_length=255, null=True)
    lastname = models.CharField(max_length=255, null=True)
    address = models.TextField(null=True)
    linkedin = models.TextField(null=True)
    phone = models.CharField(max_length=255, null=True)
    referral_code = models.CharField(
        max_length=255, null=True, unique=True, db_index=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.JOB_SEEKER)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(
        max_length=255, blank=False,
        null=False, default=AUTH_PROVIDERS.get('email'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return str(self.email)

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

    def refer(self):
        return str(self.referral_code)


class Referrals(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owners_authentication_set')
    referred = models.ForeignKey(
        User, related_name='referral_authentication_set', on_delete=models.DO_NOTHING)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.created_at)


class Profile(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='profile_authentication_set')
    dob = models.DateField(null=True)
    identity = models.ImageField(
        _("Identity"), upload_to=identity_to, default='identity/default.jpg')

    def __str__(self):
        return self.nin
