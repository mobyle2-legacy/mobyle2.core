#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mobyle2.views import Base

from mobyle2.models.registry import set_registry_key

from pyramid.httpexceptions import HTTPFound
import os
from signal import SIGUSR2
class Home(Base):
    template = '../templates/root/home.pt'

class Pdb(Base):
    template = '../templates/root/home.pt'
    def __call__(self):
        import pdb;pdb.set_trace()  ## Breakpoint ## 

class RedirectAfterLogin(Base):
    def __call__(self):
        return HTTPFound(
            self.request.resource_url(
                self.request.root
            )
        )

class Reload(Base):
    template = '../templates/root/reload.pt'
    def __call__(self):
        req = self.request
        if(req.params.get('submitted', '0') == '1' and
           'reload' in req.params):
            os._exit(SIGUSR2)
        req.session.flash('Code reloaded')
        set_registry_key('mobyle2_need_restart', False)
        return Base.__call__(self)
# vim:set et sts=4 ts=4 tw=80:
