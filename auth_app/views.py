# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from users.models import User
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit


User = get_user_model()


@ratelimit(key='ip', rate='5/m', block=False)
def register(request):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many registration attempts. Please wait a minute.")
        return render(request, "auth/register.html")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role", "candidate")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("auth_app:register")

        user = User.objects.create_user(
            username=username,
            password=password
        )

        user.role = role
        user.save()

        messages.success(request, "Account created. You can login now.")
        return redirect("auth_app:login")

    return render(request, "auth/register.html")

@require_http_methods(["GET", "POST"])
@ratelimit(key='ip', rate='10/m', block=False)
def custom_login(request):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many login attempts. Please wait a minute.")
        return render(request, 'auth/login.html')

    print("METHOD:", request.method)
    print("POST DATA:", request.POST)

    if request.user.is_authenticated:
        return redirect('auth_app:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print("USERNAME:", username)
        print("PASSWORD:", password)

        user = authenticate(request, username=username, password=password)

        print("AUTH RESULT:", user)

        if user is not None:
            login(request, user)
            return redirect('auth_app:dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'auth/login.html')

@login_required
def dashboard(request):
    """Unified user dashboard"""
    user = request.user
    role = (getattr(user, "role", "") or "").strip().lower()

    if user.is_superuser:
        return redirect('custom_admin:dashboard')

    from jobs.models import Job
    from applications.models import Application

    context = {
        'role': role
    }

    if role == "employer":
        jobs = Job.objects.filter(employer=user)
        applications = Application.objects.filter(job__employer=user).select_related(
            'job',
            'candidate'
        ).order_by('-applied_at')

        context.update({
            'jobs': jobs,
            'total_jobs': jobs.count(),
            'total_applications': applications.count(),
            'recent_applications': applications[:10],
        })

    elif role == "candidate":
        applications = user.job_applications.select_related(
            'job',
            'job__employer'
        ).order_by('-applied_at')

        unread_notifications = list(user.notifications.filter(is_read=False))
        user.notifications.filter(is_read=False).update(is_read=True)

        context.update({
            'applications': applications,
            'total_applications': applications.count(),
            'pending_applications': applications.filter(status='pending').count(),
            'accepted_applications': applications.filter(status='accepted').count(),
            'notifications': unread_notifications,
        })

    return render(request, 'dashboards/dashboard.html', context)


@login_required
def custom_logout(request):
    """Logout user"""

    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('auth_app:login')