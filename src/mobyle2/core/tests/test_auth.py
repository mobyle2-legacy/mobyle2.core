#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import unittest
from pyramid.config import Configurator
from pyramid import testing

from mobyle2.core.models import auth
from mobyle2.core.views import auth as vauth
from mobyle2.core.tests import utils

class TestAuth(unittest.TestCase):
    layer = utils.PyramidFunctionnalLayer

    def test_creation(self):
        request = testing.DummyRequest()
        info = vauth.Add(request)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

# vim:set et sts=4 ts=4 tw=80:
