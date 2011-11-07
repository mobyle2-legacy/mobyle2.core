#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import os
from ConfigParser import ConfigParser
import random
import socket
import threading

from paste.httpserver import serve
from paste.deploy import loadapp
from sqlalchemy import create_engine

from mobyle2.core.models import DBSession
from mobyle2.core.models.init import initialize_sql

from mobyle2.core import webserver as w

D = os.path.dirname
J = os.path.join
HERE_DIR = D(D(D(D(D(D(D(__file__)))))))
CONF_DIR = J(D(D(D(D(D(D(D(__file__))))))), 'etc', 'wsgi')
CONFIG = os.path.join(CONF_DIR, 'instance.ini')

socket.setdefaulttimeout(1)

__wsgiapp__ = None
__session__ = None
__server_infos__ = {}
__app_infos__ = {}

def get_port():
    for i in range(100):
        port = random.randrange(20000,40000)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            try:
                s.connect(('localhost', port))
            except socket.error:
                return port
        finally:
            s.close()
    raise RuntimeError, "Can't find port"

def server_close(self):
     """
     Finish pending requests and shutdown the server.
     """
     self.running = False
     self.socket.close()
     self.thread_pool.shutdown(1)

def get_app():
    from mobyle2.core.tests.utils import __wsgiapp__
    if not __wsgiapp__:
        __wsgiapp__ = loadapp('config:instance.ini', relative_to = CONF_DIR)
    return __wsgiapp__

def get_running_port():
    return get_server_infos()['port']

def get_app_infos():
    if not __app_infos__.keys():
        infos = ConfigParser()
        infos.read(CONFIG)
        __app_infos__.update(infos._sections['app:projectapp'])
        __app_infos__['sqlalchemy.url'] = get_sa_url()
    return __app_infos__

def get_server_infos():
    if not __server_infos__.keys():
        infos = ConfigParser()
        infos.read(CONFIG)
        __server_infos__.update(infos._sections['server:main'])
        __server_infos__['port'] = get_port()
    return __server_infos__

def get_sa_url():
    return 'sqlite://'

def get_session():
    from mobyle2.core.tests.utils import __session__
    if not __session__:
        initialize_sql(create_engine(get_sa_url()))
        __session__ = DBSession()
    return __session__

class PyramidLayer:
    #def testStUp(self, *args, **kwargs):
    def setUp(self, *args, **kwargs):
        """
        Some global are registred there
            - session: SqlAlchemy session
        """
        # sqlalchemy intialization
        self.session = get_session()
        self.config = config = w.get_config(get_app_infos())
        self.app = config.make_wsgi_app()
    setUp = classmethod(setUp)

    def tearDown(self):
        self.session.get_bind().dispose()
    tearDown = classmethod(tearDown)

class PyramidFunctionnalLayer(PyramidLayer):
    #def testStUp(self, *args, **kwargs):
    def setUp(self, *args, **kwargs):
        """
        Some global are registred there
            - server: wsgi server
            - app: the Pylon wsgi application
        """
        # server thread
        # share just one pylons across all tests
        self.wsgiapp = get_app()
        self.sinfos = get_server_infos()
        self.server = serve(self.wsgiapp,
                            self.sinfos['host'],
                            self.sinfos['port'],
                            socket_timeout=1,
                            start_loop=False,
                           )
        def mainloop():
            self.server.server_close = server_close
            self.server.serve_forever()
        self.t = threading.Thread(target=mainloop)
        self.t.setDaemon(False)
        self.t.start()
    setUp = classmethod(setUp)

    def tearDown(self):
        self.server.server_close(self.server)
        self.t.join()
    tearDown = classmethod(tearDown)
# vim:set et sts=4 ts=4 tw=80:
