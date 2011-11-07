#!/usr/bin/env python
from pyramid.i18n import TranslationStringFactory
from pyramid.i18n import get_localizer
_ = TranslationStringFactory("mobyle2")

def auto_translate(request, string):
    localizer = get_localizer(request)
    return localizer.translate(_(string))

__ = auto_translate

def splitstrip(l):
    return [a.strip()
            for a in l.split()
            if a.strip()] 
