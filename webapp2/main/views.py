from django.shortcuts import render, redirect
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def home(request):
    if not request.session.get('username'):
        return redirect('sso_check')
    return render(request, 'home.html', {'username': request.session.get('username')})

def sso_check(request):
    logger.info("[Webapp2] Starting SSO check...")
    logger.info(f"[Webapp2] Received cookies: {request.COOKIES}")
    
    webapp1_session = request.COOKIES.get('webapp1_sessionid')
    
    if webapp1_session:
        try:
            logger.info("[Webapp2] Found webapp1 session, requesting master token...")
            response = requests.get(
                'http://localhost:8001/get-master-token/',
                cookies={'webapp1_sessionid': webapp1_session},
                headers={'X-Requested-With': 'XMLHttpRequest'}
            )
            
            logger.info(f"[Webapp2] Webapp1 response: {response.status_code}")
            logger.info(f"[Webapp2] Response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                return render(request, 'sso_prompt.html', {
                    'username': data['username'],
                    'master_token': data['master_token']
                })
                
        except Exception as e:
            logger.error(f"[Webapp2] SSO check error: {str(e)}")
    
    logger.info("[Webapp2] No SSO session found, redirecting to login")
    return redirect('login')

def sso_login(request):
    if request.method == 'POST':
        webapp1_session = request.COOKIES.get('webapp1_sessionid')
        
        if webapp1_session:
            response = requests.get(
                'http://localhost:8001/get-master-token/',
                cookies={'webapp1_sessionid': webapp1_session}
            )
            
            if response.status_code == 200:
                data = response.json()
                request.session['master_token'] = data['master_token']
                request.session['username'] = data['username']
                return redirect('home')
    
    return redirect('login')

def logout_view(request):
    request.session.flush()
    return redirect('sso_check')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            response = requests.post(
                f'{settings.AUTH_SERVER_URL}/auth/login/',
                json={
                    'username': username,
                    'password': password,
                    'device_id': 'webapp2_device'
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                request.session['master_token'] = data['master_token']
                request.session['username'] = username
                return redirect('home')
            else:
                return render(request, 'login.html', {'error': 'Invalid credentials'})
                
        except Exception as e:
            return render(request, 'login.html', {'error': str(e)})
            
    return render(request, 'login.html')
