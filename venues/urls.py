from django.urls import path
from . import views

urlpatterns = [
    path('manage/',                        views.manage_venues,         name='manage_venues'),
    path('manage/add/',                    views.venue_edit,            name='venue_add'),
    path('manage/<int:pk>/edit/',          views.venue_edit,            name='venue_edit'),
    path('manage/<int:pk>/delete/',        views.venue_delete,          name='venue_delete'),
    path('',                              views.venue_list,            name='venue_list'),
    path('<int:venue_id>/book/',          views.request_booking,       name='request_booking'),
    path('booking/<int:pk>/payment/',     views.venue_booking_payment, name='venue_booking_payment'),  # NEW
]
