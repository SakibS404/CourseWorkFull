from django.urls import path
from . import views

urlpatterns = [
    # Root URL pattern
    path('', views.root_redirect, name='root'),
    
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Role-based dashboard URLs
    path('engineer_home/', views.engineer_home, name='engineer_home'),
    path('team_leader_home/', views.team_leader_home, name='team_leader_home'),
    path('department_leader_home/', views.department_leader_home, name='department_leader_home'),
    path('senior_manager_home/', views.senior_manager_home, name='senior_manager_home'),
    path('admin_home/', views.admin_home, name='admin_home'),
    
    # Profile management
    path('profile/', views.profile, name='profile'),
    
    # Application specific URLs
    path('vote/submit/', views.submit_votes, name='submit_votes'),
    path('vote/', views.vote, name='vote'),
    path('teams/', views.team_overview, name='team_overview'),
    path('departments/', views.department_list, name='department_list'),
    path('health-check/', views.health_check, name='health_check'),
]





