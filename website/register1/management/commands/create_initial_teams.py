from django.core.management.base import BaseCommand
from register1.models import Department

class Command(BaseCommand):
    help = 'Creates initial teams in the database'

    def handle(self, *args, **kwargs):
        teams = [
            {'name': 'Team 1', 'description': 'First Development Team'},
            {'name': 'Team 2', 'description': 'Second Development Team'},
            {'name': 'Team 3', 'description': 'Third Development Team'},
        ]

        for team in teams:
            Department.objects.get_or_create(
                name=team['name'],
                defaults={'description': team['description']}
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created team "{team["name"]}"')) 