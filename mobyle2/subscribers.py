import logging
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_registry

from mobyle2.views import get_base_params

from mobyle2.models import DBSession as session
from mobyle2.models.project import Project, ProjectResource, ProjectUserRole, ProjectGroupRole, projects_dir
from mobyle2.models.registry import set_registry_key, get_registry_key, set_registry_key
from mobyle2.models.user import User

from mobyle2.utils import _
from mobyle2.utils import __
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
    request.projects_dir = projects_dir()

def regenerate_velruse_config(event):
    set_registry_key('mobyle2.needrestart', True)


def user_created(event):
    request = event.request
    user = event.user
    if not session.query(User).filter_by(id=user.id).all():
        newuser = User(base_user=user, status='a')
        session.add(newuser)
        session.commit()
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
            modified = False
            for i in res:
                modified = True
                session.delete(i)
            if modified:
                session.commit()
        except Exception, e:
            error = 'Default project for %s cannot be deleted' % usr.username
            message = '%s' % e
            if message: error += ' : %s' % message
            logging.getLogger('mobyle2.delete_user').error(error)


