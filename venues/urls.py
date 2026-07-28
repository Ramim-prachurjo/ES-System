from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.venue_list,            name='venue_list'),
    path('<int:venue_id>/book/',          views.request_booking,       name='request_booking'),
    path('booking/<int:pk>/payment/',     views.venue_booking_payment, name='venue_booking_payment'),  # NEW
]