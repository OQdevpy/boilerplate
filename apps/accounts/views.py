import os
import random
from django.http import HttpResponseRedirect
from rest_framework.response import Response
from django.urls import reverse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import generics, status, views, permissions
from apps.accounts.models import User
from apps.accounts.serializers import TwoFactorCheckSerializer, PasswordUpdateSerializer, RegisterSerializer, SetNewPasswordSerializer, \
    ResetPasswordEmailRequestSerializer, LoginSerializer, \
    LogoutSerializer, UserListSerializer, UserUpdateEmailSerializer, UserUpdateSerializer
from .permissions import IsOwnUserOrReadOnly
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.core.cache import cache


class AccountRegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        user = User.objects.get(username=user_data['username'])
        tokens = user.tokens
        user_data['tokens'] = tokens
        return Response({"success": True, "data": user_data}, status=status.HTTP_201_CREATED)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    

    def post(self, request):
        
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)
            return Response({'success': False, 'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)



class UpdatePassword(generics.UpdateAPIView):
    serializer_class = PasswordUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        user = request.user
        sz = PasswordUpdateSerializer(data=request.data, context={
                                      'user': user}, many=False)
        sz.is_valid(raise_exception=True)
        password = request.data.get('password')
        user.set_password(password)
        user.save()
        return Response({'status': True})


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        email = request.data.get('email', '')
        user = get_object_or_404(User, email=email)
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)
        current_site = get_current_site(
            request=request).domain
        relativeLink = reverse(
            'user:password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
        absurl = 'http://' + current_site + relativeLink
        email_body = f'Привет! Используйте ссылку ниже, чтобы сбросить пароль: {absurl}'
        
        send_mail(
            'Сбросить пароль',
            email_body,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        return Response({'success': 'Мы отправили вам ссылку для сброса пароля'}, status=status.HTTP_200_OK)


class PasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        id = smart_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=id)

        redirect_url = f"{settings.FRONTED_URL}/resetend"

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return HttpResponseRedirect(f'{settings.FRONTED_URL}/404' + '?token_valid=False')
                else:
                    return HttpResponseRedirect(settings.FRONTED_URL + '?token_valid=False')

            if redirect_url and len(redirect_url) > 3:
                return HttpResponseRedirect(
                    redirect_url + '?token_valid=True&message=Credentials Valid&uidb64=' + uidb64 + '&token=' + token)
            else:
                return HttpResponseRedirect(settings.FRONTED_URL + '?token_valid=False')

        except DjangoUnicodeDecodeError as identifier:
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return HttpResponseRedirect(f"{settings.FRONTED_URL}/404" + '?token_valid=False')

            except UnboundLocalError as e:
                return Response({'error': 'Token is not valid, please request a new one'},
                                status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = (permissions.AllowAny,)

    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateEmailSerializer
    permission_classes = (IsAuthenticated,)

    lookup_field = 'email'

    def update(self, request, *args, **kwargs):
        if request.user.email != kwargs.get('email'):
            return Response(f"Вы не можете изменить почту пользователя {request.user.email}",
                            status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        email = instance.email
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if status.HTTP_200_OK:
            return Response(f"Почта пользователя {email} изменен на {request.data['email']}",
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRetrieveUpdate(generics.RetrieveUpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = (IsAuthenticated, IsOwnUserOrReadOnly)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        sz = UserUpdateSerializer(data=request.data, instance=user, many=False)
        sz.is_valid(raise_exception=True)
        sz.save()
        return Response(sz.data, status=status.HTTP_200_OK)


class TwoFactorAuthView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        email = request.user.email
        
        cache.set(email, code, timeout=300)
        send_mail(
            '2FA code',
            f'Your 2FA code is: {code}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return Response({'message': 'Код отправлен'}, status=status.HTTP_200_OK)


class CheckTwoFactorAuthView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TwoFactorCheckSerializer

    def post(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        email = user.email
        sz = TwoFactorCheckSerializer(data=data, many=False)
        sz.is_valid(raise_exception=True)
        code = sz.validated_data.get('code', 0)
        saved_code = cache.get(email)
        if saved_code is not None and int(saved_code) == int(code):
            user.is_verify = True
            user.save()
            cache.delete(email)
            return Response({'email': email, 'verify': True}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
