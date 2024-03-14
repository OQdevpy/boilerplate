from django.urls import include
from django.urls import path
from django.urls import re_path
# from rest_framework_simplejwt.views import TokenObtainPairView
# from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('accounts/', include('apps.accounts.urls')),


    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
