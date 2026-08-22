from django.urls import path
from . import views

app_name = 'panel'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('users/', views.users_list, name='users'),
    path('users/export/', views.export_users, name='users_export'),
    path('users/<int:user_id>/toggle-active/',
         views.toggle_user_active, name='user_toggle_active'),
    path('users/<int:user_id>/delete/', views.delete_user, name='user_delete'),
    path('reminders/', views.reminders_list, name='reminders'),
    path('reminders/export/', views.export_reminders, name='reminders_export'),
]
