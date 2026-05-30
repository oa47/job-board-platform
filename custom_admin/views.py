# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
from users.models import User

@login_required
def dashboard(request):
    """Admin dashboard"""
    if not request.user.is_superuser:
        return redirect('auth_app:dashboard')

    from jobs.models import Job
    from applications.models import Application

    context = {
        'total_jobs': Job.objects.count(),
        'total_applications': Application.objects.count(),
        'total_users': User.objects.count(),
        'recent_jobs': Job.objects.select_related('employer').order_by('-created_at')[:5],
        'recent_applications': Application.objects.select_related(
            'job',
            'candidate'
        ).order_by('-applied_at')[:5],
    }

    return render(request, 'custom_admin/dashboard.html', context)
