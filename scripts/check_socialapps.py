import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','teamsuffer.settings')
import django
django.setup()
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
apps = SocialApp.objects.all()
print('SocialApp count:', apps.count())
for a in apps:
    print('id=', a.id, 'provider=', a.provider, 'name=', a.name, 'sites=', list(a.sites.values_list('domain', flat=True)))
print('SITE_ID setting:', __import__('django.conf').conf.settings.SITE_ID)
try:
    current_site = Site.objects.get(id=__import__('django.conf').conf.settings.SITE_ID)
    print('Current Site:', current_site.id, current_site.domain)
except Exception as e:
    print('Could not get current site:', e)
