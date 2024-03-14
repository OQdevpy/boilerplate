from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from rest_framework_simplejwt.tokens import RefreshToken
from .manager import AccountManager
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("user", "Пользователь"),
        ("admin", "Администратор"),
    )
    GENDER = (
        ("male", "Мужской"),
        ("female", "Женский"),
    )
    email = models.EmailField(verbose_name="email", max_length=60,
                              unique=True, db_index=True, blank=True, null=True)
    username = models.CharField(
        max_length=50, unique=True, verbose_name="логин")
    first_name = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Фамилия")
    middle_name = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Отчество")
    gender = models.CharField(
        max_length=30, choices=GENDER, blank=True, null=True, verbose_name="Пол")
    role = models.CharField(
        max_length=30, choices=ROLE_CHOICES, default="patient", verbose_name="Роль")
    date_joined = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации")
    last_login = models.DateTimeField(
        auto_now=True, verbose_name="Последний вход")
    phone_number = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Номер телефона")
    birth_date = models.DateField(
        blank=True, null=True, verbose_name="Дата рождения")
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_verify = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name",]

    objects = AccountManager()

    avatar = models.ImageField(upload_to="users/%Y/%m/", blank=True, null=True)

    def __str__(self):
        return self.full_name

    def has_module_perms(self, app_label):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    @property
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @property
    def image_url(self):
        if not self.avatar:
            return None
        if settings.DEBUG:
            return f'{settings.LOCAL_BASE_URL}{self.avatar.url}'
        return f'{settings.PROD_BASE_URL}{self.avatar.url}'
    
    @property
    def full_name(self):
        name = self.first_name or self.username
        if self.last_name:
            name += f" {self.last_name}"
        if self.middle_name:
            name += f" {self.middle_name}"

        return name

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

