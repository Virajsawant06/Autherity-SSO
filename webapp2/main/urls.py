from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('sso-check/', views.sso_check, name='sso_check'),
    path('sso-login/', views.sso_login, name='sso_login'),
    path('logout/', views.logout_view, name='logout'),
]