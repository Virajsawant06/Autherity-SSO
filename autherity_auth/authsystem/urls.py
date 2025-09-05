from django.urls import path
from .views import LoginView, SSOLoginView, LogoutView, VerifyTokenView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth_login'),
    path('sso-login/', SSOLoginView.as_view(), name='auth_sso_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('verify/', VerifyTokenView.as_view(), name='verify_token'),
]
