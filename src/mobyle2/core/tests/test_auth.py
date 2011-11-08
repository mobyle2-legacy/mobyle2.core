#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import unittest
from pyramid import testing

from mobyle2.core.models import auth
from mobyle2.core.views import auth as vauth
from mobyle2.core.tests import utils


class TestAuth(utils.PyramidTestCase):
    layer = utils.PyramidLayer

    def __init__(self,*args):
        unittest.TestCase.__init__(self,*args)

    def test_creation_openid(self):
        request = utils.DummyRequest(
            post = {'auth_backend':'openid',
                    'description':'testd',
                    'enabled':False,
                    'key':'k',
                    'name':'openid',
                    'secret':'s',
                   }
        )
        info = vauth.Add(request)()

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
# vim:set et sts=4 ts=4 tw=80:
