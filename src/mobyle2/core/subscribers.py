import logging
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_registry

from mobyle2.core.views import get_base_params

from mobyle2.core.models import DBSession as session
from mobyle2.core.models.project import Project, ProjectRessource, ProjectUserRole, ProjectGroupRole
from mobyle2.core.models.registry import set_registry_key
from mobyle2.core.models.user import User

from mobyle2.core.utils import _
from mobyle2.core.utils import __
from sqlalchemy import exc

def add_renderer_globals(event):
    params = get_base_params(event=event)
    request = event['request']
    if request:
        event['_'] = request.translate
        event['localizer'] = request.localizer
        event.update(params)

def add_globals(event):
    request = event.request
    localizer = get_localizer(request)
    def auto_translate(string):
        return __(request, string)
    request.localizer = localizer
    request.translate = auto_translate
    request.projects_dir = request.registry.settings['mobyle2.projects_dir']

def regenerate_velruse_config(event):
    set_registry_key('mobyle2.needrestart', True)


def user_created(event):
    request = event.request
    user = event.user
    if not session.query(User).filter_by(id=user.id).all():
        newuser = User(id=user.id, status='a')
        session.add(newuser)
        session.commit()
        # try to create a default project
        will, tries, project = -1, 10 , None 
        message = ''
        while tries:
            tries -= 1
            will += 1
            try:
                pname = 'Default project of %s' % user.username
                if will:
                    pname = '%s (%s)' % (pname, will)
                registry = request.registry
                project = Project.create(pname, _('Default project created on sign in'), newuser, registry=registry)
                session.add(project)
                session.commit() 
                break
            except Exception, e:
                message = '%s' % e
                try:
                    session.rollback()
                except Exception, e:
                    pass
                tries -= 1
        if not project:
            error = 'Default project for %s cannot be created' % user.username
            if message: error += ' : %s' % message
            logging.getLogger('mobyle2.create_user').error(error)
            request.session.flash(error, 'error')
    else:
        message = _(u'a user with this id %d already exists' % user.id)
        request.session.flash(message, 'error')

def user_deleted(event):
    request = event.request
    usr = event.user
    # delete user projects and associated acls.
    for p in User.by_id(usr.id).projects[:]:
        try:
            res = []
            res.extend(ProjectGroupRole.by_resource(p))
            res.extend(ProjectUserRole.by_resource(p))
            res.append(p)
            for i in res:
                session.delete(i)
                session.commit()
        except Exception, e:
            error = 'Default project for %s cannot be deleted' % usr.username
            message = '%s' % e
            if message: error += ' : %s' % message
            logging.getLogger('mobyle2.delete_user').error(error)


