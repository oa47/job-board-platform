from django.urls import path
from . import views

#url conifig
urlpatterns = [
    path('hello/',views.say_hello)
]