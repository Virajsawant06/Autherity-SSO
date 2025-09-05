from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.sso_login, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Add logout URL
    path('get-master-token/', views.get_master_token, name='get_master_token'),
]
