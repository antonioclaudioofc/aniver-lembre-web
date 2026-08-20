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
]
