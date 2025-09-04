from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from .models import User, DeviceInfo, MasterToken, SessionToken, LoginLog
from django.utils import timezone
import uuid

def get_client_ip(request):
    # Utility to get client IP address from request
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Login with username/password, generate master token, return it
        """
        username = request.data.get('username')
        password = request.data.get('password')
        device_id = request.data.get('device_id')
        user_agent = request.headers.get('User-Agent', '')

        user = authenticate(username=username, password=password)
        if user is not None:
            # Get or create device info
            device, _ = DeviceInfo.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'user_agent': user_agent,
                    'ip_address': get_client_ip(request)
                }
            )
            # Create MasterToken valid 30 days
            master_token = MasterToken.objects.create(
                user=user,
                device=device,
                expires_at=timezone.now() + timezone.timedelta(days=30),
                is_active=True
            )
            LoginLog.objects.create(user=user, device=device, ip_address=get_client_ip(request), action='login', success=True)
            return Response({'master_token': str(master_token.token)}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class SSOLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        SSO login using master token, generate session token
        """
        master_token_str = request.data.get('master_token')
        device_id = request.data.get('device_id')
        user_agent = request.headers.get('User-Agent', '')
        if not master_token_str:
            return Response({'error': 'Master token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            master_token = MasterToken.objects.get(token=master_token_str, is_active=True, expires_at__gte=timezone.now())
        except MasterToken.DoesNotExist:
            return Response({'error': 'Invalid or expired master token'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get or create device info for this session
        device, _ = DeviceInfo.objects.get_or_create(
            device_id=device_id,
            defaults={'user_agent': user_agent, 'ip_address': get_client_ip(request)}
        )
        # Create session token valid 1 hour
        session_token = SessionToken.objects.create(
            user=master_token.user,
            master_token=master_token,
            device=device,
            expires_at=timezone.now() + timezone.timedelta(hours=1),
            is_active=True
        )
        LoginLog.objects.create(user=master_token.user, device=device, ip_address=get_client_ip(request), action='sso_login', success=True)

        return Response({'session_token': str(session_token.token)}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    def post(self, request):
        """
        Invalidate session token to logout current session without affecting master token
        """
        session_token_str = request.data.get('session_token')
        if not session_token_str:
            return Response({'error': 'Session token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            session_token = SessionToken.objects.get(token=session_token_str, is_active=True)
            session_token.is_active = False
            session_token.save()
            LoginLog.objects.create(user=session_token.user, device=session_token.device, ip_address=get_client_ip(request), action='logout', success=True)
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except SessionToken.DoesNotExist:
            return Response({'error': 'Invalid session token'}, status=status.HTTP_401_UNAUTHORIZED)
