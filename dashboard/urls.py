from django.urls import path
from . import views

urlpatterns = [
    path('',                                        views.admin_dashboard,    name='admin_dashboard'),
    path('booking/<int:booking_id>/approve/',        views.approve_booking,    name='approve_booking'),
    path('booking/<int:booking_id>/reject/',         views.reject_booking,     name='reject_booking'),
    path('tournament/<int:tournament_id>/approve/',  views.approve_tournament, name='approve_tournament'),
    path('tournament/<int:tournament_id>/reject/',   views.reject_tournament,  name='reject_tournament'),
    path('organizer/history/',                       views.organizer_history,  name='organizer_history'),  # NEW
    path('history/',                                 views.admin_history,      name='admin_history'),
    path('branding/',                                views.platform_branding,  name='platform_branding'),
]
