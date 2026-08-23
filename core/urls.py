from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('reminders/', include('reminders.urls')),
    path('panel/', include('panel.urls')),
    path('admin/', admin.site.urls),
]
