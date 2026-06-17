# scraper_data/management/commands/debug_admin.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.urls import reverse

class Command(BaseCommand):
    help = 'Debug admin configuration'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Checking admin configuration...')
        
        # Check if admin users exist
        user_count = User.objects.count()
        self.stdout.write(f'📊 Total users: {user_count}')
        
        if user_count == 0:
            self.stdout.write(self.style.WARNING('⚠️ No users found! Create a superuser.'))
            self.stdout.write('Run: python manage.py createsuperuser')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Users found'))
        
        # Check admin URLs
        try:
            admin_url = reverse('admin:index')
            self.stdout.write(f'🔗 Admin index URL: {admin_url}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Admin URL error: {e}'))
        
        # Check template configuration
        from django.conf import settings
        template_dirs = settings.TEMPLATES[0].get('DIRS', [])
        self.stdout.write(f'📁 Template dirs: {template_dirs}')
        
        app_dirs = settings.TEMPLATES[0].get('APP_DIRS', False)
        self.stdout.write(f'📁 APP_DIRS: {app_dirs}')
        
        self.stdout.write(self.style.SUCCESS('✅ Debug complete'))