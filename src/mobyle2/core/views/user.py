#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

from ordereddict import OrderedDict

from pyramid.renderers import render_to_response
from pyramid.response import Response

from mobyle2.core.models import auth
from mobyle2.core.models import DBSession as session
from mobyle2.core.models import registry as r
from mobyle2.core.views import Base as bBase, get_base_params as get_base_params
from mobyle2.core import validator as v
from mobyle2.core.utils import _

from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
import deform
import colander

from mobyle2.core.events import RegenerateVelruseConfigEvent

from mobyle2.core.models.registry import get_registry_key

bool_values = {
    '1': True,
    '0': False,
    1: True,
    0: False,
    'true': True,
    'false': False,
}

class Base(bBase):
    def get_base_params(self):
        params = {'view': self}
        params.update(get_base_params(self))
        return params

    def __call__(self):
        params = self.get_base_params()
        return render_to_response(self.template, params, self.request)

class Home(Base):
    template ='../templates/user/user_home.pt'


# vim:set et sts=4 ts=4 tw=0:
