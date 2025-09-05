import requests
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

# URL of your Auth Server SSO endpoints
AUTH_SERVER_LOGIN_URL = 'http://localhost:8000/auth/login/'
AUTH_SERVER_SSO_LOGIN_URL = 'http://localhost:8000/auth/sso-login/'

def sso_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        device_id = request.POST.get('device_id', 'webapp1_device')
        
        print(f"Sending login request with: username={username}, device_id={device_id}")
        login_data = {
            'username': username,
            'password': password,
            'device_id': device_id
        }
        
        response = requests.post('http://localhost:8000/auth/login/', json=login_data)
           
        
        print('Auth server status:', response.status_code)
        print('Auth server response text:', repr(response.text))

        try:
            data = response.json()
            master_token = data.get('master_token')
            if response.status_code == 200:
                master_token = response.json()['master_token']
                print('Received master token:', master_token)
                request.session['master_token'] = master_token
                request.session['device_id'] = device_id
                request.session['username'] = username

                response = redirect('home')
                response.set_cookie('master_token', master_token, httponly=True)
                response.set_cookie('device_id', device_id)
                return response
                
            else:
                error = data.get('error', 'Login failed')
        except Exception as e:
            print('JSON decode error:', e)
            error = 'Auth server did not return valid JSON.'


        # if response.status_code == 200:
        #     master_token = response.json()['master_token']

        #     # Store token in session and set as cookie
        #     request.session['master_token'] = master_token
        #     request.session['device_id'] = device_id
        #     request.session['username'] = username

        #     resp = redirect('home')
        #     resp.set_cookie('master_token', master_token, httponly=True, secure=True)
        #     resp.set_cookie('device_id', device_id)
        #     return resp
        # else:
        #     error = response.json().get('error', 'Login failed')
        #     return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')


@csrf_exempt  # For demo only, add proper CSRF for production
def sso_auto_login(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        master_token = data.get('master_token')
        device_id = data.get('device_id')

        # Verify master token with Auth Server
        response = requests.post(AUTH_SERVER_SSO_LOGIN_URL, json={
            'master_token': master_token,
            'device_id': device_id
        })
        if response.status_code == 200:
            session_token = response.json().get('session_token')
            request.session['session_token'] = session_token
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'SSO failed'}, status=401)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def home(request):
    username = request.session.get('username')
    session_token = request.session.get('session_token')

    if not username or not session_token:
        return redirect('login')

    context = {
        'username': username,
        'session_token': session_token,
    }
    return render(request, 'home.html', context)


def logout_view(request):
    request.session.flush()  # Clear all session data
    resp = redirect('login')
    resp.delete_cookie('master_token')
    resp.delete_cookie('device_id')
    return resp
