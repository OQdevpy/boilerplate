from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode
from apps.accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    password_confirmation = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    first_name = serializers.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "email",
                  'role',  "password", "password_confirmation") 

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirmation = attrs.pop("password_confirmation")
        if password != password_confirmation:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match"})
        return attrs



class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField(
        max_length=68, min_length=6, write_only=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    def get_tokens(self, obj):
        
        user = User.objects.get(username=obj['username'])
        return {
            'refresh': user.tokens['refresh'],
            'access': user.tokens['access']
        }

    class Meta:
        model = User
        fields = ("id", "username", "password", 'tokens')

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed(
                {"success": False, "message": "Неверный логин или пароль"})

        attrs["user"] = user
        return attrs


class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email']


class PasswordUpdateSerializer(serializers.Serializer):
    password_true = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    password2 = serializers.CharField(
        min_length=6, max_length=68, write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        password_true = attrs.get('password_true')
        password2 = attrs.get('password')
        user = self.context.get('user')
        user = authenticate(username=user.username, password=password_true)
        if not user:
            raise AuthenticationFailed(
                {"success": False, "message": "Password is incorrect"})
        if password != password2:
            raise AuthenticationFailed(
                {"success": False, "message": "Passwords do not match"})
        attrs['user'] = user
        return attrs


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)
            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_message = {
        'bad_token': ('Token is expired or invalid')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):

        try:
            RefreshToken(self.token).blacklist()

        except TokenError:
            self.fail('bad_token')


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class UserUpdateEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email",)


class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("first_name", "last_name", "middle_name",
                  "gender", "birth_date", 'email', 'role', )


class TwoFactorCheckSerializer(serializers.Serializer):
    code = serializers.IntegerField(write_only=True,)
