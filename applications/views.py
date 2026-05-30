from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from jobs.models import Job
from .models import Application, ApplicationStatus
from .forms import ApplicationForm
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

@method_decorator(ratelimit(key='user', rate='5/m', block=False), name='post')
class ApplyJobView(LoginRequiredMixin, View):
    def handle_no_permission(self):
        messages.warning(self.request, "You must have an account and be signed in to apply for a job.")
        return super().handle_no_permission()

    def get(self, request, job_id):
        if getattr(request.user, 'role', '') != 'candidate':
            messages.error(request, "Only candidates can apply for jobs.")
            return redirect('jobs:detail', pk=job_id)
            
        job = get_object_or_404(Job, pk=job_id)
        
        if Application.objects.filter(job=job, candidate=request.user).exists():
            messages.info(request, "You have already applied for this job.")
            return redirect('jobs:detail', pk=job.pk)
            
        form = ApplicationForm()
        return render(request, 'applications/apply.html', {'form': form, 'job': job})

    def post(self, request, job_id):
        if getattr(request, 'limited', False):
            messages.error(request, "You are applying too fast. Please wait a minute.")
            return redirect('jobs:detail', pk=job_id)

        if getattr(request.user, 'role', '') != 'candidate':
            messages.error(request, "Only candidates can apply for jobs.")
            return redirect('jobs:detail', pk=job_id)
            
        job = get_object_or_404(Job, pk=job_id)
        
        if Application.objects.filter(job=job, candidate=request.user).exists():
            messages.info(request, "You have already applied for this job.")
            return redirect('jobs:detail', pk=job.pk)
            
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.save()
            messages.success(request, "Application submitted successfully!")
            return redirect('auth_app:dashboard')
            
        return render(request, 'applications/apply.html', {'form': form, 'job': job})

class ApplicationReviewView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if getattr(request.user, 'role', '') != 'employer':
            return redirect('auth_app:dashboard')
            
        application = get_object_or_404(Application, pk=pk, job__employer=request.user)
        return render(request, 'applications/review.html', {'application': application})

    def post(self, request, pk):
        if getattr(request.user, 'role', '') != 'employer':
            return redirect('auth_app:dashboard')
            
        application = get_object_or_404(Application, pk=pk, job__employer=request.user)
        status = request.POST.get('status')
        
        if status in [ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED]:
            if application.status != status:
                application.status = status
                application.save()
                
                from users.models import Notification
                status_text = "accepted" if status == ApplicationStatus.ACCEPTED else "rejected"
                Notification.objects.create(
                    user=application.candidate,
                    message=f"Your application for {application.job.title} has been {status_text}."
                )
                
            messages.success(request, f"Application marked as {status}.")
            
        return redirect('auth_app:dashboard')
