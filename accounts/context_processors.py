from .models import PlatformBranding


def platform_branding(request):
    return {'branding': PlatformBranding.get_solo()}
