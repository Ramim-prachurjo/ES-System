from django.urls import path
from . import views

urlpatterns = [
    path('',                                          views.team_list,           name='team_list'),
    path('browse/',                                   views.browse_teams,        name='browse_teams'),
    path('create/',                                   views.create_team,         name='create_team'),
    path('my-team/',                                  views.my_team,             name='my_team'),
    path('<int:team_id>/rename/',                     views.rename_team,         name='rename_team'),
    path('<int:pk>/',                                 views.team_detail,         name='team_detail'),
    path('<int:team_id>/invite/',                     views.invite_player,       name='invite_player'),
    path('join/',                                     views.join_by_code,        name='join_by_code'),
    path('invites/',                                  views.my_invites,          name='my_invites'),
    path('invites/<int:invite_id>/<str:action>/',     views.respond_invite,      name='respond_invite'),
    path('<int:team_id>/leave/',                      views.leave_team,          name='leave_team'),
    path('<int:team_id>/transfer/<int:user_id>/',     views.transfer_captain,    name='transfer_captain'),
    path('<int:team_id>/request-join/',               views.request_to_join,     name='request_to_join'),
    path('join-requests/',                            views.my_join_requests,    name='my_join_requests'),
    path('join-request/<int:req_id>/<str:action>/',   views.handle_join_request, name='handle_join_request'),
    path('<int:team_id>/remove/<int:user_id>/',       views.remove_member,       name='remove_member'),
]




