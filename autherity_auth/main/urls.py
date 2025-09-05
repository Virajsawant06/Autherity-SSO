from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.sso_login, name='login'),
    path('sso-auto-login/', views.sso_auto_login, name='sso_auto_login'),
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
]