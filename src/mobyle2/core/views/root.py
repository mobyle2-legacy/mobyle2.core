#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mobyle2.core.views import Base
import os
from signal import SIGUSR2
class Home(Base):
    template = 'root/home.mako'
 
class Reload(Base):
    template = 'root/reload.mako'
    def __call__(self):
        req = self.request
        if(req.params.get('submitted', '0') == '1' and
           'reload' in req.params):
            os._exit(SIGUSR2) 
        req.session.flash('Code reloaded')
        return Base.__call__(self)
# vim:set et sts=4 ts=4 tw=80:
