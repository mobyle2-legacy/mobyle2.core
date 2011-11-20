from pyramid.i18n import get_localizer
from mobyle2.core.utils import __

from mobyle2.core.views import get_base_params

from mobyle2.core.models.auth import AuthenticationBackend
from mobyle2.core.models import DBSession as session

def add_renderer_globals(event):
    params = get_base_params(event=event)
    request = event['request']
    if request:
        event['_'] = request.translate
        event['localizer'] = request.localizer
        event.update(params)

def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)
    def auto_translate(string):
        return __(request, string)
    request.localizer = localizer
    request.translate = auto_translate


def regenerate_velruse_config(event):
    """Regenerate the velruse authentication configuration file with the backends specified on the website database."""
    registry = event.registry

