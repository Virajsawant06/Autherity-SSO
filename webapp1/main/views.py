import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from .models import User, SessionToken
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

AUTH_SERVER_SSO_LOGIN_URL = 'http://localhost:8000/auth/sso-login/'

logger = logging.getLogger(__name__)

@csrf_exempt
def sso_auto_login(request):
    
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        master_token = data.get('master_token')
        device_id = data.get('device_id')

        # Verify on Auth Server
        response = requests.post(f'{settings.AUTH_SERVER_URL}/auth/sso-login/', json={
            'master_token': master_token,
            'device_id': device_id
        })
        if response.status_code == 200:
            session_token = response.json()['session_token']
            request.session['session_token'] = session_token
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'SSO failed'}, status=401)

    return JsonResponse({'error': 'invalid request'}, status=400)

def sso_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        device_id = request.POST.get('device_id', 'webapp1_device')

        try:
            response = requests.post(
                'http://localhost:8000/auth/login/',
                json={
                    'username': username,
                    'password': password,
                    'device_id': device_id
                },
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Auth server status: {response.status_code}")
            print(f"Auth server response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                # Extract master token from the response string
                master_token = data['master_token']
                if isinstance(master_token, str) and 'MasterToken' in master_token:
                    # Extract UUID from the string
                    import re
                    token_match = re.search(r'\((.*?)\)', master_token)
                    if token_match:
                        master_token = token_match.group(1)
                
                request.session['master_token'] = master_token
                request.session['username'] = username
                request.session.save()  # Explicitly save the session
                return redirect('home')
            else:
                error = response.json().get('error', 'Login failed')
                return render(request, 'login.html', {'error': error})

        except Exception as e:
            print(f"Login error: {str(e)}")
            return render(request, 'login.html', {'error': str(e)})

    return render(request, 'login.html')


def home(request):
    username = request.session.get('username')
    master_token = request.session.get('master_token')

    print(f"Session data - username: {username}, token exists: {bool(master_token)}")  # Debug

    if not username or not master_token:
        return redirect('login')

    context = {
        'username': username,
    }
    return render(request, 'home.html', context)


def logout_view(request):
    # Clear session data
    request.session.flush()
    return redirect('login')

@csrf_exempt
def get_master_token(request):
    master_token = request.session.get('master_token')
    username = request.session.get('username')
    
    logger.info(f"[Webapp1] Token request from {request.META.get('HTTP_REFERER')}")
    logger.info(f"[Webapp1] Session data: token={master_token}, username={username}")
    logger.info(f"[Webapp1] Cookies: {request.COOKIES}")

    if master_token and username:
        response_data = {
            'master_token': master_token,
            'username': username
        }
        logger.info(f"[Webapp1] Sending token response: {response_data}")
        return JsonResponse(response_data)
    
    logger.error("[Webapp1] No active session found")
    return JsonResponse({'error': 'No active session'}, status=401)
