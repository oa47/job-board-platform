from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Job
from .forms import JobForm


class JobListView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        jobs = Job.objects.filter(is_active=True).select_related('employer')
        
        if query:
            from django.db.models import Q
            jobs = jobs.filter(
                Q(title__icontains=query) | 
                Q(location__icontains=query) | 
                Q(description__icontains=query)
            )
            
        context = {
            'jobs': jobs,
            'query': query,
        }
        return render(request, 'jobs/list.html', context)


class JobDetailView(View):
    def get(self, request, pk):
        job = get_object_or_404(Job.objects.select_related('employer'), pk=pk)
        context = {
            'job': job,
        }
        return render(request, 'jobs/detail.html', context)


def index(request):
    """Home page showing featured jobs"""
    jobs = Job.objects.filter(is_active=True).select_related('employer').order_by('-created_at')[:6]
    context = {
        'jobs': jobs,
    }
    return render(request, 'index.html', context)


class JobCreateView(LoginRequiredMixin, View):
    def handle_no_permission(self):
        messages.warning(self.request, "You must have an account and be signed in to post a job.")
        return super().handle_no_permission()

    def get(self, request):
        if getattr(request.user, 'role', '') != 'employer':
            messages.error(request, "Only employers can post jobs.")
            return redirect('auth_app:dashboard')
        form = JobForm()
        return render(request, 'jobs/create.html', {'form': form})

    def post(self, request):
        if getattr(request.user, 'role', '') != 'employer':
            messages.error(request, "Only employers can post jobs.")
            return redirect('auth_app:dashboard')
        
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()
            messages.success(request, "Job posted successfully!")
            return redirect('jobs:detail', pk=job.pk)
        return render(request, 'jobs/create.html', {'form': form})

class JobApplicantsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if getattr(request.user, 'role', '') != 'employer':
            return redirect('auth_app:dashboard')
            
        job = get_object_or_404(Job, pk=pk, employer=request.user)
        applications = job.applications.select_related('candidate').order_by('-applied_at')
        
        context = {
            'job': job,
            'applications': applications,
        }
        return render(request, 'jobs/applicants.html', context)


class JobDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if getattr(request.user, 'role', '') != 'employer':
            return redirect('auth_app:dashboard')
        
        job = get_object_or_404(Job, pk=pk, employer=request.user)
        job.delete()
        messages.success(request, "Job posting permanently deleted.")
        return redirect('auth_app:dashboard')


class JobToggleStatusView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if getattr(request.user, 'role', '') != 'employer':
            return redirect('auth_app:dashboard')
        
        job = get_object_or_404(Job, pk=pk, employer=request.user)
        job.is_active = not job.is_active
        job.save()
        status_msg = "activated" if job.is_active else "closed"
        messages.success(request, f"Job has been {status_msg}.")
        return redirect('auth_app:dashboard')