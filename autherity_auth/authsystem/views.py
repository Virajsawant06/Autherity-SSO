from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        device_id = request.data.get('device_id', 'default_device')

        print(f"Login attempt - username: {username}, device_id: {device_id}")

        try:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Deactivate old tokens for this device
                MasterToken.objects.filter(
                    user=user,
                    device__device_id=device_id
                ).update(is_active=False)

                # Generate new token
                token = uuid.uuid4()
                expires_at = timezone.now() + timezone.timedelta(days=7)
                
                device, _ = DeviceInfo.objects.get_or_create(
                    user=user,
                    device_id=device_id
                )
                
                master_token = MasterToken.objects.create(
                    user=user,
                    device=device,
                    token=token,
                    expires_at=expires_at,
                    is_active=True
                )

                return Response({
                    'master_token': str(token),
                    'expires_at': expires_at.isoformat()
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

        except Exception as e:
            print(f"Login error: {str(e)}")
            return Response(
                {'error': 'Authentication failed'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )


@method_decorator(csrf_exempt, name='dispatch')
class SSOLoginView(APIView):
    permission_classes = [AllowAny]  # Changed from permissions.AllowAny

    def post(self, request):
        """
        SSO login using master token, generate session token
        """
        master_token_str = request.data.get('master_token')
        device_id = request.data.get('device_id')
        
        if not master_token_str:
            return Response({'error': 'Master token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            master_token = MasterToken.objects.get(token=master_token_str, is_active=True, expires_at__gte=timezone.now())
        except MasterToken.DoesNotExist:
            return Response({'error': 'Invalid or expired master token'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get or create device info for this session
        device, _ = DeviceInfo.objects.get_or_create(
            device_id=device_id,
            defaults={'ip_address': get_client_ip(request)}
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

class VerifyTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        master_token = request.data.get('master_token')
        print(f"Verifying token: {master_token}")

        try:
            token_obj = MasterToken.objects.filter(token=master_token).first()
            if token_obj and token_obj.is_valid():
                return Response({
                    'username': token_obj.user.username,
                    'valid': True
                })
            return Response({'error': 'Invalid or expired token'}, status=401)
        except Exception as e:
            print(f"Token verification error: {str(e)}")
            return Response({'error': 'Invalid token format'}, status=400)
