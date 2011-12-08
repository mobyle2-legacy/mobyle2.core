#!/usr/bin/env python
from pyramid.i18n import TranslationStringFactory
from pyramid.i18n import get_localizer
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

