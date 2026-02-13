
import os
import sys
import django

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teamsuffer.settings")
django.setup()

from django.contrib.auth.models import User

try:
    if not User.objects.filter(username='testadmin').exists():
        User.objects.create_superuser('testadmin', 'admin@example.com', 'password123')
        print("Created testadmin")
    else:
        u = User.objects.get(username='testadmin')
        u.set_password('password123')
        u.save()
        print("Updated testadmin password")
except Exception as e:
    print(f"Error: {e}")
