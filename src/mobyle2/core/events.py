#!/usr/bin/env python
from zope.interface import implements, Interface

class IRegenerateVelruseConfigEvent(Interface):
    """Marker interface"""

class RegenerateVelruseConfigEvent(object):
    implements(IRegenerateVelruseConfigEvent)
    def __init__(self, request):
        self.request = request

# vim:set et sts=4 ts=4 tw=0:
