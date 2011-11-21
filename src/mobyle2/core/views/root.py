#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mobyle2.core.views import Base
from mobyle2.core.utils import waiting_for_reload

from pyramid.httpexceptions import HTTPFound
import os
from signal import SIGUSR2
class Home(Base):
    template = '../templates/root/home.pt'

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
        waiting_for_reload(reset=True)
        return Base.__call__(self)
# vim:set et sts=4 ts=4 tw=80:
