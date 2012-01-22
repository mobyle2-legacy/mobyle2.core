from lxml import etree
from glob import glob
import sys
import logging
from mobyle2.core.models.project import Project, Service
from mobyle2.core.models import DBSession as session

public_project = Project.get_public_project()
public_user = public_project.owner

def insert_service(name,description,package,classification):
    s = Service()
    s.name = name
    s.description = description
    s.package = package
    s.server = public_project.servers[0]
    s.project = public_project
    s.classification = classification
    s.type = 'program'
    session.add(s)
    session.commit()

def parse_service(path):
    s_xml = etree.parse(path)
    d = {}
    d['name'] = s_xml.xpath('/*/head/name/text()')[0]
    d['description'] = ''.join(s_xml.xpath('/*/head/doc/description//text()'))
    d['classification'] = s_xml.xpath('/*/head/category/text()')[0]
    d['package'] = s_xml.xpath('/*/head/package/name/text()')[0]
    return d

for path in glob('/home/hmenager/*.xml'):
    try:
        logging.info("parsing %s..." % path)
        s_d = parse_service(path)
        insert_service(s_d['name'],s_d['description'],s_d['package'],s_d['classification'])
    except:
        logging.error("Error while parsing file %s." % path, exc_info=True)
