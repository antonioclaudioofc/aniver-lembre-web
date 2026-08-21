from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name="register"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('profile/', views.profile, name="profile"),
    path('verify-email/', views.verify_email, name="verify_email"),
    path('password-reset/', views.password_reset_request,
         name="password_reset_request"),
    path('password-reset/confirm/', views.password_reset_confirm,
         name="password_reset_confirm"),
    path('password-reset/new-password/', views.password_reset_new_password,
         name="password_reset_new_password"),
]
