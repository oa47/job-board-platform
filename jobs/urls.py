from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.index, name='index'),
    path('jobs/', views.JobListView.as_view(), name='list'),
    path('jobs/create/', views.JobCreateView.as_view(), name='create'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='detail'),
    path('jobs/<int:pk>/applicants/', views.JobApplicantsView.as_view(), name='applicants'),
]