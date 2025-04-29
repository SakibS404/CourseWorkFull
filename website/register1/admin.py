from django.contrib import admin  # this block of code is to import the admin class
from .models import Person, Department, Team, Vote # this block of code is to import the  person model into the admin class


# this block of code is used to place the persons model within the admin page, holds all databases for this project
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('department', 'user', 'joined_at')
    list_filter = ('department', 'joined_at')
    search_fields = ('user__username', 'department__name')

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('username', 'job_title', 'department')
    list_filter = ('job_title', 'department')
    search_fields = ('username', 'user__email')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'username', 
        'team_name', 
        'timestamp',
        'Team_Progress',
        'Team_Collaboration',
        'Code_Quality',
        'Work_Environment',
        'Communication',
        'Project_Timeline'
    )
    list_filter = (
        'team_name', 
        'timestamp',
        'Team_Progress',
        'Team_Collaboration',
        'Code_Quality',
        'Work_Environment',
        'Communication',
        'Project_Timeline'
    )
    search_fields = ('user__username', 'username', 'team_name')
    readonly_fields = ('username', 'team_name')

    def save_model(self, request, obj, form, change):
        if not obj.username:
            obj.username = obj.user.username
        team = obj.user.team_memberships.first()
        if team:
            obj.team_name = team.name
        super().save_model(request, obj, form, change)



















        
###############################################################################
#
# Reference:
#
# Simple UE is better then complex (2020). Extend User in Django part 2: Token Auth. 
#[online] YouTube. 
#Available at: https://www.youtube.com/watch?v=HDiMliULC18 [Accessed 25 Apr. 2025].
#
############################################################################
 
