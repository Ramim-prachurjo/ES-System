from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/player/', views.player_profile, name='player_profile'),
    path('profile/player/<int:user_id>/', views.view_player_profile, name='view_player_profile'),
    path('organizer/<int:user_id>/', views.view_organizer_profile, name='view_organizer_profile'),
    path('profile/organizer/', views.organizer_profile, name='organizer_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.txt',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password-reset/done/',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/password-reset/complete/',
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('support/faq/', views.faq, name='faq'),
    path('support/terms-and-conditions/', views.terms_conditions, name='terms_conditions'),
    path('support/privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
