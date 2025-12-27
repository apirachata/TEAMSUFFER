from django import template
from django.urls import reverse
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

register = template.Library()

@register.simple_tag(takes_context=True)
def social_apps(context):
    """Return SocialApp queryset for the current site."""
    try:
        site = Site.objects.get_current()
    except Exception:
        site = None
    if site:
        return SocialApp.objects.filter(sites=site)
    return SocialApp.objects.none()

@register.simple_tag(takes_context=True)
def provider_login_url(context, provider_id):
    """Generate login URL for a social provider."""
    try:
        return reverse('socialaccount_login', args=[provider_id])
    except Exception:
        return '#'
