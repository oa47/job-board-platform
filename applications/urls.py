from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/<int:job_id>/', views.ApplyJobView.as_view(), name='apply'),
    path('review/<int:pk>/', views.ApplicationReviewView.as_view(), name='review'),
]
