from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Create a SocialApp and attach it to the current Site (useful to enable social buttons locally)'

    def add_arguments(self, parser):
        parser.add_argument('--provider', default='google', help='Provider id (default: google)')
        parser.add_argument('--name', default='Google', help='Name for the SocialApp')
        parser.add_argument('--client-id', dest='client_id', default='', help='Client ID for the Social App')
        parser.add_argument('--secret', dest='secret', default='', help='Client Secret for the Social App')
        parser.add_argument('--site-id', dest='site_id', type=int, default=None, help='Site ID to attach to (default: settings.SITE_ID)')
        parser.add_argument('--replace', action='store_true', help='Replace an existing SocialApp for the provider if it exists')

    def handle(self, *args, **options):
        provider = options['provider']
        name = options['name']
        client_id = options['client_id']
        secret = options['secret']
        site_id = options['site_id'] or getattr(settings, 'SITE_ID', None)
        replace = options['replace']

        if site_id is None:
            self.stderr.write('No site id configured (provide --site-id or set SITE_ID in settings).')
            return

        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            self.stderr.write(f'Site with id={site_id} does not exist')
            return

        existing = SocialApp.objects.filter(provider=provider)
        if existing.exists():
            if replace:
                existing.delete()
                self.stdout.write(f'Removed existing SocialApp(s) for provider={provider}')
            else:
                self.stdout.write(f'Found existing SocialApp(s) for provider={provider}. Use --replace to recreate. Aborting.')
                return

        app = SocialApp.objects.create(
            provider=provider,
            name=name,
            client_id=client_id or f'{provider}-client-id-placeholder',
            secret=secret or f'{provider}-secret-placeholder'
        )
        app.sites.add(site)
        app.save()

        self.stdout.write(self.style.SUCCESS(f'Created SocialApp {app} and attached to site {site.domain} (id={site.id}).'))
        if not client_id or not secret:
            self.stdout.write(self.style.WARNING('Client ID or Secret were empty; update the SocialApp in the admin with real credentials to enable OAuth flows.'))