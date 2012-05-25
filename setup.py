# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
#README = open(os.path.join(here, 'README.txt')).read()
#CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()


requires = [
        "apex",
        "CherryPy",
        "colander",
        "cryptacular",
        "Chameleon",
        "plone.i18n",# for the I18NNormalizer utility
        "translationstring",
        "Babel",
        'zope.dottedname',
        "lingua",
        "deform",
        "demjson",
        "egenix-mx-base",
        "elementtree",
        "gunicorn",
        "lxml",
        "zope.testbrowser",
        "ordereddict",
#        "Paste",
        "PasteDeploy",
        "PIL",
        "psycopg2",
        "pylint",
        "pyramid",
        "pyramid_beaker",
        "pyramid_debugtoolbar",
        "pyramid_formalchemy",
        "fa.jquery",
        "pyramid_extdirect",
        "pyramid_who",
        "pyramid_xmlrpc",
        "pyramid_zcml",
        "python-ldap",
        "repoze.retry",
        "repoze.tm2",
        "repoze.tm2",
        "repoze.vhm",
        "PasteScript",
        "PasteDeploy",
        "simplejson",
        "sqlalchemy",
        "zope.component",
        "WebError",
        "WebOb",
    ],



setup(name='mobyle2',
      version='0.0',
      description='mobyle2 core',
      dependency_links = ['https://github.com/mobyle2/apex/tarball/master#egg=apex'],
      #long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="mobyle2",
      entry_points = """\
      [paste.app_factory]
      main = mobyle2:webserver.wsgi_app_factory
      """,
      paster_plugins=['pyramid'],
      
      )

