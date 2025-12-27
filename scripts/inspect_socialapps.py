import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teamsuffer.settings')
django.setup()

from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def main():
    print('SITE_ID =', settings.SITE_ID)
    print('\nSites:')
    for s in Site.objects.all():
        print(f'  id={s.id} domain={s.domain!r} name={s.name!r}')

    print('\nSocialApps:')
    for sa in SocialApp.objects.all():
        site_ids = list(sa.sites.values_list('id', flat=True))
        print(f'  id={sa.id} name={sa.name!r} provider={sa.provider!r} client_id_set={bool(sa.client_id)} sites={site_ids}')

if __name__ == '__main__':
    main()
