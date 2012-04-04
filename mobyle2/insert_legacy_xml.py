# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from lxml import etree
from glob import glob
import sys, os
import logging
import shutil

from pyramid.paster import bootstrap

from mobyle2.models.project import Project, Service
from mobyle2.models import DBSession as session

public_project = Project.get_public_project()
public_user = public_project.owner

def insert_update_service(name,stype,description,package,classification):
    """Insert a service in the database as belonging
    to the local - and only - server of the public project."""
    try:
	svc = session.query(Service).filter_by(name=name,
				             server=public_project.servers[0],
				             project=public_project).first()
	if not svc:
	    logging.info("service %s new, adding to the server" % name)
            svc = Service()
            svc.name = name
            svc.server = public_project.servers[0]
            svc.project = public_project
	    session.add(svc)
	else:
	    logging.info("service %s already here, updating" % name)
        svc.description = description
        svc.package = package
        svc.classification = classification
        svc.type = stype
        session.commit()
        return svc
    except:
	session.rollback()
	raise

def parse_service(path):
    """Parse a Mobyle1 xml file to get the mandatory information
    used in the database """
    s_xml = etree.parse(path)
    d = {}
    d['type'] = s_xml.xpath('/*')[0].xpath('local-name()')
    d['name'] = s_xml.xpath('/*/head/name/text()')[0]
    d['description'] = ' '.join([s.strip().replace('\n','') for s in s_xml.xpath('/*/head/doc/description//text()')]).strip()
    #TODO: a service can have multiple classification items - this should be fixed in the model first.
    d['classification'] = (s_xml.xpath('/*/head/category/text()')+[''])[0]
    d['package'] = ''.join(s_xml.xpath('/*/head/package/name/text()'))
    return d

def import_mobyle1_service(path):
    """Import a single service."""
    try:
        logging.info("parsing %s..." % path)
        s_d = parse_service(path)
        service = insert_update_service(s_d['name'], s_d['type'], s_d['description'],\
                s_d['package'],s_d['classification'])
        shutil.copyfile(path,service.xml_file)
    except:
        logging.error("Error while parsing file %s." % path, exc_info=True)

def import_mobyle1_service_directory(dir_path):
    """Import a whole directory - will scan all files
    with an XML extension inside"""
    for path in glob(os.path.join(dir_path,'*.xml')):
        import_mobyle1_service(path)
