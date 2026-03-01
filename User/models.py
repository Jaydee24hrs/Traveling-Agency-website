from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group, Permission


# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', "tyktt")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    DOCUMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    )

    USER_TYPE = (
        ("tyktt", "tyktt"),
        ('affiliate', 'affiliate')
    )

    SALUTATION_CHOICES = (
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Miss', 'Miss'),
        ('Ms', 'Ms'),
        ('Dr', 'Dr'),
        ('Prof', 'Prof'),
        # Add more salutation choices as needed
    )
    ## Personal Information
    email = models.EmailField(verbose_name='email', max_length=255, unique=True)
    username = models.CharField(max_length=250)
    business_name = models.CharField(max_length=250, blank=True)
    first_name = models.CharField(max_length=250, blank=True, null=True)
    middle_name = models.CharField(max_length=250, blank=True, null=True)
    phone = models.CharField(max_length=250, blank=True, null=True)
    phone_number_dial_code = models.CharField(max_length=250, blank=True, null=True, default="234")
    city = models.CharField(max_length=250, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    postal_code = models.CharField(max_length=250, blank=True, null=True)
    last_name = models.CharField(max_length=250, blank=True, null=True)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, null=True, blank=True)
    salutation = models.CharField(max_length=50, choices=SALUTATION_CHOICES, blank=True)
    bio = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)
    dob = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=250, null=True, blank=True)
    country = models.CharField(max_length=250, null=True, blank=True)

    # User Type
    POSITION_CHOICE = [
        ("Support", "Support"),
        ("Admin", "Admin"),
        ("Manager", "Manager"),
        ("Finance", "Finance"),
    ]
    position = models.CharField(max_length=50, choices=POSITION_CHOICE, default="Support")
    user_type = models.CharField(max_length=20, choices=USER_TYPE, default='affiliate')
    profile_pic = models.ImageField(blank=True, null=True)
    created_on = models.DateField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateField(auto_now=True, null=True, blank=True)
    is_director = models.BooleanField(default=False, null=True, blank=False)
    access_type = models.CharField(max_length=100, default="User")

    # User Doc
    ID_CHOICE = [
        ('Passport', 'Passport'),
        ('National Identification Card', 'National Identification Card'),
    ]
    means_of_identification = models.CharField(max_length=255, choices=ID_CHOICE)
    status = models.CharField(max_length=255, choices=DOCUMENT_STATUS_CHOICES, default="pending")
    means_of_identification_file = models.FileField(upload_to="user_means_of_identification", null=True, blank=True)
    rejection_reason = models.TextField(max_length=100, null=True, blank=True)
    replace_reason = models.TextField(max_length=100, null=True, blank=True)
    otp = models.CharField(max_length=10, null=True, blank=True)
    is_verified = models.BooleanField(default=False, null=True, blank=True)

    # User Groups and Permissions
    groups = models.ManyToManyField(Group, related_name='custom_user_set', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_set', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


    objects = CustomUserManager()

    def __str__(self):
        return self.email

class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name="User_OTP")
    otp = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    edited_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    used = models.BooleanField(default=False)

class Customer(models.Model):
    first_name = models.CharField(max_length=250, null=True, blank=True)
    last_name = models.CharField(max_length=250, null=True, blank=True)
    date_of_birth = models.DateField(max_length=250, null=True, blank=True)
    middle_name = models.CharField(max_length=250, null=True, blank=True)
    email = models.EmailField(unique=True, primary_key=True,default="example@example.com")
    country_code = models.CharField(max_length=5, null=True, blank=True)
    phone_number = models.CharField(max_length=250, null=True, blank=True)
    
    def __str__(self):
        return f'{self.email}'
