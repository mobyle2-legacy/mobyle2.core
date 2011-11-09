from pyramid.i18n import get_localizer
from mobyle2.core.utils import __

def add_renderer_globals(event):
    request = event['request']
    if request:
        event['_'] = request.translate
        event['localizer'] = request.localizer

def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)
    def auto_translate(string):
        return __(request, string)
    request.localizer = localizer
    request.translate = auto_translate
