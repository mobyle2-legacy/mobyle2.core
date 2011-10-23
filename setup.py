#!/usr/bin/env python
# -*- coding: utf-8 -
from setuptools import setup, find_packages

name = 'mobyle2.core'
setup(
    name=name,
    namespace_packages=[         'mobyle2',
         'mobyle2.core',],

    version = '1.0',
    description = 'Project mobyle2',
    long_description = '' ,
    author = 'Mathieu Le Marec- Pasquet',
    author_email = 'mpa <mpa@makina-corpus.com>',
    license = 'GPL',
    keywords = '',
    url='http://pypi.python.org/pypi/%s' % name,
    install_requires = [            "pyramid_extdirect",
            "psycopg2",
            "egenix-mx-base",
            "sqlalchemy",
            "PIL",
            "pyramid_who",
            "demjson",
            "simplejson",
            "lxml",
            "elementtree",
            "pylint",
            "pyramid_debugtoolbar",
            "python-ldap",
            "pyramid_zcml",
            "pyramid_xmlrpc",
            "pyramid",
            "repoze.tm2",
            "ordereddict",
            "cryptacular",
            "PasteDeploy",
            "Paste",
            "WebOb",
            "WebError",
            "repoze.vhm",
            "CherryPy",
            "gunicorn",
                       ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    # Make setuptools include all data files under version control,
    # svn and CVS by default
    include_package_data=True,
    zip_safe=False,
    extras_require={'test': ['IPython', 'zope.testing'
    #, 'mocker'
    ]},
    entry_points = {
        'paste.app_factory':  [
            'main=mobyle2.core.webserver:wsgi_app_factory' ,
        ],
        'console_scripts': [
            '%s=mobyle2.core.webserver:main' % name ,
        ],
    }
)


