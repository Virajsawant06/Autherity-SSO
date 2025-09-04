from django.urls import path
from .views import LoginView, SSOLoginView, LogoutView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('sso-login/', SSOLoginView.as_view(), name='sso-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
