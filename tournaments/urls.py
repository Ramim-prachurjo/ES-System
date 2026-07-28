from django.urls import path
from . import views

urlpatterns = [
    path('',                                        views.tournament_list,      name='tournament_list'),
    path('create/',                                 views.create_tournament,    name='create_tournament'),
    path('<int:pk>/',                               views.tournament_detail,    name='tournament_detail'),

    # ✅ ADD THIS LINE
    path('<int:pk>/payment/', views.tournament_payment_info, name='tournament_payment_info'),

    path('<int:tournament_id>/apply/<int:team_id>/', views.apply_to_tournament, name='apply_to_tournament'),
    path('application/<int:application_id>/approve/', views.approve_application, name='approve_application'),
    path('application/<int:application_id>/reject/',  views.reject_application,  name='reject_application'),
]
