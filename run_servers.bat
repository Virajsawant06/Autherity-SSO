@echo off
echo Starting Django Servers...

start cmd /k "cd autherity_auth && python manage.py runserver 8000"
timeout /t 5
start cmd /k "cd webapp1 && python manage.py runserver 8001"
timeout /t 5
start cmd /k "cd webapp2 && python manage.py runserver 8002"

echo All servers are running:
echo Auth Server: http://localhost:8000
echo WebApp1: http://localhost:8001
echo WebApp2: http://localhost:8002