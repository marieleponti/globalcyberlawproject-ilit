"""nat_state_vis_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from core import health

# The admin path is configurable so it can be moved off /admin/ in production.
ADMIN_URL = os.environ.get("DJANGO_ADMIN_URL", "admin/").lstrip("/")

urlpatterns = [
    path('healthz', health.healthz, name='healthz'),
    path('readyz', health.readyz, name='readyz'),
    path(ADMIN_URL, admin.site.urls),
    path('', include('core.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
