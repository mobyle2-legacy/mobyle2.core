#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import unittest
from pyramid.config import Configurator
from pyramid import testing


from mobyle2.core.models import initialize_sql, DBSession, Base
from mobyle2.core.models.project import Project

def _initTestingDB():
    from sqlalchemy import create_engine
    initialize_sql(create_engine('sqlite://'))
    session = DBSession()
    return session

class TestProject(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()

    def test_creation(self):
        import pdb;pdb.set_trace()  ## Breakpoint ##


    #def test_it(self):
    #    from tutorial.views import my_view
    #    request = testing.DummyRequest()
    #    info = my_view(request)
    #    self.assertEqual(info['root'].name, 'root')
    #    self.assertEqual(info['project'], 'tutorial') 

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

# vim:set et sts=4 ts=4 tw=80:
