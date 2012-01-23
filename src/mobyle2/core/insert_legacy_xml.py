# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from lxml import etree
from glob import glob
import sys, os
import logging
import shutil

from pyramid.paster import bootstrap

from mobyle2.core.models.project import Project, Service
from mobyle2.core.models import DBSession as session

public_project = Project.get_public_project()
public_user = public_project.owner

def insert_service(name,stype,description,package,classification):
    """Insert a service in the database as belonging
    to the local - and only - server of the public project."""
    s = Service()
    s.name = name
    s.description = description
    s.package = package
    s.server = public_project.servers[0]
    s.project = public_project
    s.classification = classification
    #TODO: service is assumed to be a program
    s.type = stype
    session.add(s)
    session.commit()
    return s

def parse_service(path):
    """Parse a Mobyle1 xml file to get the mandatory information
    used in the database """
    s_xml = etree.parse(path)
    d = {}
    d['type'] = s_xml.xpath('/*')[0].xpath('local-name()')
    d['name'] = s_xml.xpath('/*/head/name/text()')[0]
    d['description'] = ''.join(s_xml.xpath('/*/head/doc/description//text()'))
    d['classification'] = s_xml.xpath('/*/head/category/text()')[0]
    d['package'] = ''.join(s_xml.xpath('/*/head/package/name/text()'))
    return d

def import_mobyle1_service(path):
    """Import a single service."""
    try:
        logging.info("parsing %s..." % path)
        s_d = parse_service(path)
        service = insert_service(s_d['name'], s_d['type'], s_d['description'],\
                s_d['package'],s_d['classification'])
        shutil.copyfile(path,service.xml_file)
    except:
        logging.error("Error while parsing file %s." % path, exc_info=True)

def import_mobyle1_service_directory(dir_path):
    """Import a whole directory - will scan all files
    with an XML extension inside"""
    for path in glob(os.path.join(dir_path,'*.xml')):
        import_mobyle1_service(path)
