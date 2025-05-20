# management/commands/create_superadmin.py
from django.core.management.base import BaseCommand
from diverge.models import User
import uuid

class Command(BaseCommand):
    help = 'Cria um usuário superadmin'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'Usuário com email {email} já existe.'))
            return
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type='SUPERADMIN',
            rm='SA-' + str(uuid.uuid4())[:8],
            is_staff=True,
            is_superuser=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'Superadmin {username} criado com sucesso!'))