#importing relevant extensions
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render



#this code declares the job title drop down options which will be stored in the Persons model database
JOB_TITLE_CHOICES = [
    ('engineer', 'Engineer'),
    ('team_leader', 'Team Leader'),
    ('department_leader', 'Department Leader'),
    ('senior_manager', 'Senior Manager'),
    ('admin', 'Admin'),
]

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100, default='Default Team')  # Adding name field with default
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teams')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['department', 'user']

    def __str__(self):
        return f"{self.name} - {self.user.username} ({self.department.name})"

#creating a persons model. This is to store the job titles within the database as it is not provided by django in the  user model
class Person(models.Model):

    # creating a one to one relationship between user model and persons model (making them interconnected)
    user =models.OneToOneField(User,on_delete=models.CASCADE,related_name='person')

    username =models.CharField(max_length=200)
    
    job_title=models.CharField(max_length=200,choices=JOB_TITLE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='members')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Create team membership when department is assigned
        if self.department:
            team_name = f"{self.department.name} Team"
            Team.objects.get_or_create(
                department=self.department,
                user=self.user,
                defaults={'name': team_name}
            )

    def __str__(self):
        return f"{self.username} - {self.job_title} - {self.department.name if self.department else 'No Team'}"










###############################################################################
#Reference:
#Tech With Tim (2019). Django Tutorial - User Registration & Sign Up Page. 
#[online] YouTube. 
#Available at: https://www.youtube.com/watch?v=Ev5xgwndmfc 
#[Accessed 20 Apr. 2025]
#
############################################################################
 

class Vote(models.Model):
    # User and metadata fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=200, null=True, blank=True)
    team_name = models.CharField(max_length=200, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    # Vote categories as attributes with color values
    Team_Progress = models.CharField(max_length=5, null=True, blank=True)      # Will store "Green", "Amber", "Red"
    Team_Collaboration = models.CharField(max_length=5, null=True, blank=True)  # Will store "Green", "Amber", "Red"
    Code_Quality = models.CharField(max_length=5, null=True, blank=True)        # Will store "Green", "Amber", "Red"
    Work_Environment = models.CharField(max_length=5, null=True, blank=True)    # Will store "Green", "Amber", "Red"
    Communication = models.CharField(max_length=5, null=True, blank=True)       # Will store "Green", "Amber", "Red"
    Project_Timeline = models.CharField(max_length=5, null=True, blank=True)    # Will store "Green", "Amber", "Red"

    class Meta:
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        # Auto-populate username and team_name if not set
        if not self.username:
            self.username = self.user.username if self.user else None
        
        # Get team information
        team = self.user.team_memberships.first()
        if team:
            self.team_name = team.name
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.team_name}) - {self.timestamp.strftime('%Y-%m-%d')}"

@login_required
def health_check(request):
    """Display health check results."""
    today = timezone.now().date()
    
    categories = [
        'Team_Progress',
        'Team_Collaboration',
        'Code_Quality',
        'Work_Environment',
        'Communication',
        'Project_Timeline'
    ]
    
    try:
        # Get the user's team
        user_team = request.user.team_memberships.first()
        
        if not user_team:
            context = {
                'error_message': "You are not assigned to any team. Please contact your administrator.",
                'today': today
            }
            return render(request, 'register1/health_check.html', context)
        
        # Get votes for today from users in the same team
        today_votes = Vote.objects.filter(
            timestamp__date=today,
            team_name=user_team.name
        ).select_related('user')  # Add select_related to optimize queries
        
        # Initialize vote statistics with individual votes
        vote_stats = {
            category: {
                'display_name': category.replace('_', ' '),
                'labels': ['Green', 'Amber', 'Red'],
                'counts': [0, 0, 0],
                'total_votes': 0,
                'individual_votes': []  # Add list to store individual votes
            } for category in categories
        }
        
        # Process votes
        for vote in today_votes:
            for category in categories:
                value = getattr(vote, category)
                if value:
                    color_index = {'Green': 0, 'Amber': 1, 'Red': 2}[value]
                    vote_stats[category]['counts'][color_index] += 1
                    vote_stats[category]['total_votes'] += 1
                    # Add individual vote with username
                    vote_stats[category]['individual_votes'].append({
                        'username': vote.username,
                        'vote': value,
                        'timestamp': vote.timestamp.strftime('%H:%M')
                    })
        
        # Get team members count
        team_members_count = Team.objects.filter(
            name=user_team.name
        ).count()
        
        context = {
            'vote_stats': vote_stats,
            'team': user_team,
            'team_members_count': team_members_count,
            'votes_submitted': today_votes.count(),
            'today': today
        }
        
    except Exception as e:
        context = {
            'error_message': f"Error retrieving vote information: {str(e)}",
            'today': today
        }
    
    return render(request, 'register1/health_check.html', context)
 

