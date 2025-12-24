from .models import UserProfile
from django.contrib.auth.decorators import login_required
@login_required
def edit_profile_view(request):
	profile = UserProfile.objects.get(user=request.user)
	if request.method == 'POST':
		phone = request.POST.get('phone')
		if phone:
			profile.phone = phone
			profile.save()
	return render(request, 'accounts/edit_profile.html', {'profile': profile})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import UserProfile

def register_view(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		phone = request.POST.get('phone', '')
		is_driver = request.POST.get('is_driver', False)
		user = User.objects.create_user(username=username, password=password)
		UserProfile.objects.create(user=user, phone=phone, is_driver=is_driver)
		return redirect('login')
	return render(request, 'accounts/register.html')

def login_view(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)
		if user:
			login(request, user)
			return redirect('home')
		else:
			return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
	return render(request, 'accounts/login.html')

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

@require_POST
@csrf_protect
def logout_view(request):
	"""Securely log out a user.

	Django 5 admin now requires a POST with a CSRF token for logout to mitigate CSRF attacks.
	We mirror that requirement for the public logout endpoint. Frontend should submit a
	<form method="post" action="/accounts/logout/"> with {% csrf_token %}.
	"""
	logout(request)
	return redirect('login')
