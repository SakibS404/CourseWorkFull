#importing relevant extensions
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from .forms import RegisterForm, LoginForm
from .models import Person, Vote, Department, Team
import json
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder





#creates a view function for register1 app, to handle http request and response 
def register(request):
    """Handle user registration with department assignment."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Person.objects.create(
                user=user,
                username=user.username,
                job_title=form.cleaned_data['job_title'],
                department=form.cleaned_data['department']
            )
            group, _ = Group.objects.get_or_create(name='Engineer')
            user.groups.add(group)
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register1/signup.html', {'form': form})

def user_login(request):
    """Handle user login with email/username support."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']
            
            # Try username first, then email
            user = authenticate(request, username=identifier, password=password)
            if not user:
                try:
                    user_obj = User.objects.get(email=identifier)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user and user.is_active:
                login(request, user)
                try:
                    person = Person.objects.get(user=user)
                    return redirect(f'{person.job_title}_home')
                except Person.DoesNotExist:
                    messages.error(request, 'User profile not found.')
                    return redirect('login')
            else:
                form.add_error(None, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'register1/login.html', {'form': form})

def user_logout(request):
    """Handle user logout and clear session data."""
    if 'has_voted' in request.session:
        del request.session['has_voted']
    logout(request)
    return redirect('login')

def check_job_title(view_func):
    """Decorator to check if user has the required job title."""
    def wrapper(request, *args, **kwargs):
        try:
            person = Person.objects.get(user=request.user)
            required_title = view_func.__name__.replace('_home', '')
            if person.job_title != required_title:
                messages.error(request, f'You do not have {required_title.title()} permissions.')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        except Person.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('login')
    return wrapper

@login_required
@check_job_title
def engineer_home(request):
    return render(request, 'register1/engineer_home.html')

@login_required
@check_job_title
def team_leader_home(request):
    return render(request, 'register1/team_leader_home.html')

@login_required
@check_job_title
def department_leader_home(request):
    return render(request, 'register1/department_leader.html')

@login_required
@check_job_title
def senior_manager_home(request):
    return render(request, 'register1/senior_manager.html')

@login_required
@check_job_title
def admin_home(request):
    return render(request, 'register1/admin.html')

@login_required
def profile(request):
    """Handle user profile updates."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        
        user = authenticate(request, username=request.user.username, password=password)
        if user is not None:
            if username and username != user.username:
                if User.objects.filter(username=username).exclude(id=user.id).exists():
                    messages.error(request, 'Username already exists.')
                    return redirect('profile')
                user.username = username
                # Update Person model username as well
                try:
                    person = Person.objects.get(user=user)
                    person.username = username
                    person.save()
                except Person.DoesNotExist:
                    messages.warning(request, 'User profile not found, but account updated.')
            
            if email:
                # Check if email is already in use
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    messages.error(request, 'Email already in use.')
                    return redirect('profile')
                user.email = email
            
            if new_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)
            
            user.save()
            messages.success(request, 'Profile updated successfully!')
        else:
            messages.error(request, 'Incorrect current password.')
        return redirect('profile')
    
    return render(request, 'register1/profile.html')

@login_required
def department_list(request):
    """Display list of departments for authorized users."""
    person = get_object_or_404(Person, user=request.user)
    if person.job_title not in ['admin', 'senior_manager', 'department_leader']:
        messages.error(request, 'You do not have permission to view all departments.')
        return redirect('team_overview')
    departments = Department.objects.all()
    return render(request, 'register1/department_list.html', {'departments': departments})

@login_required
def team_overview(request):
    """Display team overview for the logged-in user."""
    person = get_object_or_404(Person, user=request.user)
    try:
        # Get team members from the same department
        team_members = Person.objects.filter(department=person.department)
        context = {
            'department': person.department,
            'team_members': team_members,
        }
    except Exception as e:
        context = {'error_message': 'Error retrieving team information.'}
    
    return render(request, 'register1/team_overview.html', context)

@login_required
def vote(request):
    """Handle team health check voting."""
    vote_categories = [
        {
            'name': 'Team_Progress',
            'display_name': 'Team Progress',
            'question': 'the current team progress'
        },
        {
            'name': 'Team_Collaboration',
            'display_name': 'Team Collaboration',
            'question': 'team collaboration'
        },
        {
            'name': 'Code_Quality',
            'display_name': 'Code Quality',
            'question': 'the current code quality'
        },
        {
            'name': 'Work_Environment',
            'display_name': 'Work Environment',
            'question': 'the work environment'
        },
        {
            'name': 'Communication',
            'display_name': 'Communication',
            'question': 'team communication'
        },
        {
            'name': 'Project_Timeline',
            'display_name': 'Project Timeline',
            'question': 'the project timeline'
        }
    ]

    if request.session.get('has_voted', False):
        if request.method == 'POST':
            return JsonResponse({
                'status': 'error',
                'message': 'You have already voted in this session.'
            }, status=403)
        messages.warning(request, 'You have already submitted your vote for this session.')
        return render(request, 'register1/vote.html', {'vote_categories': vote_categories})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            votes = data.get('votes', [])
            
            if not votes:
                return JsonResponse({'status': 'error', 'message': 'No votes provided'}, status=400)
            
            # Save votes
            today = timezone.now().date()
            Vote.objects.filter(user=request.user, timestamp__date=today).delete()
            
            # Create a new vote object with all categories
            vote_data_dict = {vote['category']: vote['vote'].capitalize() for vote in votes}
            
            new_vote = Vote(
                user=request.user,
                Team_Progress=vote_data_dict.get('Team_Progress'),
                Team_Collaboration=vote_data_dict.get('Team_Collaboration'),
                Code_Quality=vote_data_dict.get('Code_Quality'),
                Work_Environment=vote_data_dict.get('Work_Environment'),
                Communication=vote_data_dict.get('Communication'),
                Project_Timeline=vote_data_dict.get('Project_Timeline'),
                timestamp=timezone.now()
            )
            new_vote.save()
            
            request.session['has_voted'] = True
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'message': 'Votes recorded successfully',
                'redirect_url': reverse('vote')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return render(request, 'register1/vote.html', {'vote_categories': vote_categories})

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
        team = request.user.team_memberships.first()
        
        if not team:
            context = {
                'error_message': "You are not assigned to any team. Please contact your administrator.",
                'today': today
            }
            return render(request, 'register1/health_check.html', context)
        
        # Get votes for today from users in the same team
        today_votes = Vote.objects.filter(
            timestamp__date=today,
            team_name=team.name
        ).select_related('user')
        
        # Initialize vote statistics
        vote_stats = {}
        for category in categories:
            votes = [getattr(vote, category) for vote in today_votes if getattr(vote, category)]
            green_count = sum(1 for v in votes if v == 'Green')
            amber_count = sum(1 for v in votes if v == 'Amber')
            red_count = sum(1 for v in votes if v == 'Red')
            
            vote_stats[category] = {
                'display_name': category.replace('_', ' '),
                'data': [green_count, amber_count, red_count],
                'total_votes': len(votes)
            }
        
        # If no votes yet, initialize with zero counts
        if not vote_stats:
            for category in categories:
                vote_stats[category] = {
                    'display_name': category.replace('_', ' '),
                    'data': [0, 0, 0],
                    'total_votes': 0
                }
        
        # Convert vote_stats to JSON in a way that's safe for JavaScript
        vote_stats_json = json.dumps(vote_stats)
        
        context = {
            'vote_stats': vote_stats_json,
            'team': team,
            'team_members_count': Team.objects.filter(name=team.name).count(),
            'votes_submitted': today_votes.count(),
            'today': today
        }
        
    except Exception as e:
        context = {
            'error_message': f"Error retrieving vote information: {str(e)}",
            'today': today
        }
    
    return render(request, 'register1/health_check.html', context)

@login_required
def submit_votes(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            votes = data.get('votes', [])
            
            if not votes:
                return JsonResponse({'success': False, 'message': 'No votes provided'}, status=400)
            
            # Save votes
            today = timezone.now().date()
            Vote.objects.filter(user=request.user, timestamp__date=today).delete()
            
            # Create a new vote object with all categories
            vote_data_dict = {vote['category']: vote['vote'].capitalize() for vote in votes}  # Store "Green", "Amber", "Red"
            
            new_vote = Vote(
                user=request.user,
                Team_Progress=vote_data_dict.get('Team_Progress'),
                Team_Collaboration=vote_data_dict.get('Team_Collaboration'),
                Code_Quality=vote_data_dict.get('Code_Quality'),
                Work_Environment=vote_data_dict.get('Work_Environment'),
                Communication=vote_data_dict.get('Communication'),
                Project_Timeline=vote_data_dict.get('Project_Timeline'),
                timestamp=timezone.now()
            )
            new_vote.save()
            
            request.session['has_voted'] = True
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'message': 'Votes recorded successfully',
                'redirect_url': reverse('health_check')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    # Define vote_categories here or redirect to vote view
    return redirect('vote')  # Changed to redirect instead of render

def root_redirect(request):
    """Redirect root URL to appropriate page based on authentication status."""
    if request.user.is_authenticated:
        try:
            person = Person.objects.get(user=request.user)
            return redirect(f'{person.job_title}_home')
        except Person.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('login')
    return redirect('login')











        
###############################################################################
#
# Reference:
#
# Simple UE is better then complex (2020). Extend User in Django part 2: Token Auth. 
# [online] YouTube. 
# Available at: https://www.youtube.com/watch?v=HDiMliULC18 [Accessed 25 Apr. 2025].
#
#
#
# Tech With Tim (2019). Django Tutorial - User Registration & Sign Up Page. 
# [online] YouTube. 
# Available at: https://www.youtube.com/watch?v=Ev5xgwndmfc 
# [Accessed 20 Apr. 2025]
#
############################################################################
 
    
    
