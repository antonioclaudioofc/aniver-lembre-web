from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('aniversariantes/', views.people, name='people'),
    path('create-reminder/', views.create_reminder, name='create_reminder'),
    path('reminder/<int:reminder_id>/delete/', views.delete_reminder,
         name='delete_reminder'),
]
