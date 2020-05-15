"""ridesadmin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from rides_admin import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login),
    path('loginValidation/', views.loginValidation),
    path('logout/', views.logout),
    path('', views.getDashboardData),
    path('userverification', views.getUserVerificationData),
    path('dashboard', views.getDashboardData),
    path('verifyUserMatrix', views.verifyUserMatrix),
    path('rejectUserMatrix', views.rejectUserMatrix),
    path('verifyUserLicense', views.verifyUserLicense),
    path('rejectUserLicense', views.rejectUserLicense),
    path('user', views.getAllUsers),
    path('ride', views.getAllRides),
    path('userDetail', views.getUserDetail),
    path('rideDetail', views.getRideDetail),
    path('positionTracking', views.positionTracking)
]
