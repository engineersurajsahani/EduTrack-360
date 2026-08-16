from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UnifiedLoginForm, UserProfileForm
from .models import User, FacultyProfile
from core.decorators import admin_required

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:redirect_view')
        
    if request.method == 'POST':
        form = UnifiedLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:redirect_view')
        else:
            messages.error(request, "Invalid username/PRN or password.")
    else:
        form = UnifiedLoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user)
        
    return render(request, 'accounts/profile.html', {'form': form, 'user_obj': user})
