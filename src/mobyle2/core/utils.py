#!/usr/bin/env python
from pyramid.i18n import TranslationStringFactory
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_registry
_ = TranslationStringFactory("mobyle2")

def auto_translate(request, string):
    localizer = get_localizer(request)
    untranslated = _(string)
    if string and isinstance(string, basestring):
        if hasattr(string, 'domain'):
            untranslated = string
    return localizer.translate(untranslated)

__ = auto_translate

def splitstrip(l):
    return [a.strip()
            for a in l.split()
            if a.strip()] 

def asbool(value):
    if isinstance(value, basestring):
        if value.lower()  in ['y', 'yes', 'ok', '1', 'true', 't']:
            value = True
        elif value.lower()  in ['n', 'no', 'ko', '0', 'false', 'f']:
            value = False
    if isinstance(value, int):
        value = bool(value)
    return value 


def mobyle2_settings(key=None, default=None, registry=None):
    """ Gets an apex setting if the key is set.
        If no key it set, returns all the apex settings.

        Some settings have issue with a Nonetype value error,
        you can set the default to fix this issue.
    """
    if not registry:
        registry = get_current_registry()
    settings = registry.settings

    if key:
        return settings.get('mobyle2.%s' % key, default)
    else:
        apex_settings = []
        for k, v in settings.items():
            if k.startswith('mobyle2.'):
                apex_settings.append({k.split('.')[1]: v})
        return apex_settings 

