from django.urls import path
from . import views

app_name = 'reminders'

urlpatterns = [
    path('run-check/', views.run_due_reminders, name='run_check'),
]
