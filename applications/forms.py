from django import forms
from .models import Application

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Write your cover letter here...'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }
