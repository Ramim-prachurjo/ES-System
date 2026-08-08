from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views

urlpatterns = [
    path('admin/',           admin.site.urls),
    path('accounts/',        include('accounts.urls')),
    path('venues/',          include('venues.urls')),
    path('dashboard/',       include('dashboard.urls')),
    path('teams/',           include('teams.urls')),
    path('tournaments/',     include('tournaments.urls')),
    path('notifications/',   include('notifications.urls')),   # NEW
    path('',                 account_views.landing, name='home'),
]
