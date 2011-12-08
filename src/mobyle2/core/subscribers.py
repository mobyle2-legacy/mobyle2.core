import logging
from pyramid.i18n import get_localizer

from mobyle2.core.views import get_base_params

from mobyle2.core.models import DBSession as session
from mobyle2.core.models.project import Project
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

def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)
    def auto_translate(string):
        return __(request, string)
    request.localizer = localizer
    request.translate = auto_translate

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
        while tries:
            tries -= 1
            will += 1
            try:
                pname = 'Default project of %s' % user.username
                if will:
                    pname = '%s (%s)' % (pname, will)
                project = Project(pname, _('Default project created on sign in'), newuser)
                session.add(project)
                session.commit() 
                break
            except Exception, e:
                try:
                    session.rollback()
                except Exception, e:
                    pass
                tries -= 1
        if not project:
            error = 'Default project for cannot be created: %s' % user.username
            logging.getLogger('mobyle2.create_user').error(error)
            request.session.flash(error, 'error')
    else:
        message = _(u'a user with this id %d already exists' % user.id)
        request.session.flash(message, 'error')


