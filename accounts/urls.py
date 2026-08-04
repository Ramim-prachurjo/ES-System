from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/player/', views.player_profile, name='player_profile'),
    path('profile/player/<int:user_id>/', views.view_player_profile, name='view_player_profile'),
    path('profile/organizer/', views.organizer_profile, name='organizer_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('support/faq/', views.faq, name='faq'),
    path('support/terms-and-conditions/', views.terms_conditions, name='terms_conditions'),
    path('support/privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
