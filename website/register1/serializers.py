from rest_framework import serializers
from .models import Vote, Team, Department, Person
from django.contrib.auth.models import User
from collections import Counter

class VoteSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    class Meta:
        model = Vote
        fields = [
            'id',
            'username',
            'team_name',
            'timestamp',
            'Team_Progress',
            'Team_Collaboration',
            'Code_Quality',
            'Work_Environment',
            'Communication',
            'Project_Timeline'
        ]
        read_only_fields = ['username', 'team_name']

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def get_team_name(self, obj):
        if obj.user:
            team = obj.user.team_memberships.first()
            return team.name if team else None
        return None

    def create(self, validated_data):
        user = self.context.get('request').user if self.context.get('request') else None
        if user:
            validated_data['user'] = user
        return super().create(validated_data)

class TeamMemberSerializer(serializers.ModelSerializer):
    votes = VoteSerializer(source='vote_set', many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'votes']

class VoteSummaryMixin:
    def get_vote_stats(self, votes, field_name):
        field_votes = [getattr(v, field_name) for v in votes if getattr(v, field_name) is not None]
        if not field_votes:
            return {
                'mode': None,
                'percentages': {
                    'Red': 0,
                    'Amber': 0,
                    'Green': 0
                },
                'total_votes': 0,
                'voters': []
            }
        
        total_votes = len(field_votes)
        counter = Counter(field_votes)
        mode = counter.most_common(1)[0][0] if counter else None
        
        voters = [{'username': v.username, 'team': v.team_name} 
                 for v in votes if getattr(v, field_name) is not None]
        
        percentages = {
            'Red': round((counter['Red'] / total_votes * 100), 1) if 'Red' in counter else 0,
            'Amber': round((counter['Amber'] / total_votes * 100), 1) if 'Amber' in counter else 0,
            'Green': round((counter['Green'] / total_votes * 100), 1) if 'Green' in counter else 0
        }
        
        return {
            'mode': mode,
            'percentages': percentages,
            'total_votes': total_votes,
            'voters': voters
        }

    def get_vote_summary(self, votes):
        fields = [
            'Team_Progress',
            'Team_Collaboration',
            'Code_Quality',
            'Work_Environment',
            'Communication',
            'Project_Timeline'
        ]
        
        return {
            field: self.get_vote_stats(votes, field)
            for field in fields
        }

class TeamSerializer(serializers.ModelSerializer, VoteSummaryMixin):
    member_count = serializers.SerializerMethodField()
    vote_summary = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'member_count', 'vote_summary', 'department', 'user']

    def get_member_count(self, obj):
        return 1  # Since each team record represents one user

    def get_vote_summary(self, obj):
        team_votes = Vote.objects.filter(user=obj.user)
        return self.get_vote_summary(team_votes)

class DepartmentSerializer(serializers.ModelSerializer, VoteSummaryMixin):
    teams = TeamSerializer(many=True, read_only=True)
    team_count = serializers.SerializerMethodField()
    department_vote_summary = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'team_count', 'department_vote_summary', 'teams']

    def get_team_count(self, obj):
        return obj.teams.count()

    def get_department_vote_summary(self, obj):
        department_votes = Vote.objects.filter(user__team_memberships__department=obj)
        return self.get_vote_summary(department_votes)

class PersonSerializer(serializers.ModelSerializer):
    department_details = DepartmentSerializer(source='department', read_only=True)
    
    class Meta:
        model = Person
        fields = ['id', 'username', 'job_title', 'department', 'department_details']

class UserSerializer(serializers.ModelSerializer):
    person = PersonSerializer()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'person']
        
    def create(self, validated_data):
        person_data = validated_data.pop('person')
        user = User.objects.create(**validated_data)
        Person.objects.create(user=user, **person_data)
        return user

    def update(self, instance, validated_data):
        person_data = validated_data.pop('person', {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if person_data and hasattr(instance, 'person'):
            for attr, value in person_data.items():
                setattr(instance.person, attr, value)
            instance.person.save()
        
        return instance














        
###############################################################################
#
# Reference:
#
# Simple UE is better then complex (2020). Extend User in Django part 2: Token Auth. 
#[online] YouTube. 
#Available at: https://www.youtube.com/watch?v=HDiMliULC18 [Accessed 25 Apr. 2025].
#
############################################################################
 
        

    