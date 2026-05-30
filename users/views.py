from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Profile
from .forms import UserForm, ProfileForm


class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
        return render(request, 'users/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile
        })

    def post(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('users:profile')

        return render(request, 'users/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile
        })
