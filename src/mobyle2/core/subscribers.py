from pyramid.i18n import get_localizer
from mobyle2.core.utils import __

from mobyle2.core.views import get_base_params

from mobyle2.core.models import DBSession as session
from mobyle2.core.models.project import Project
from mobyle2.core.models.registry import set_registry_key
from mobyle2.core.models.user import User  

from mobyle2.core.utils import _
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
        newuser = User(user.id, 'a')
        session.add(newuser)
        session.commit()
        default_project = Project('Default project of %s' % user.username,
                                  'Default project created on sign in', newuser)
        session.add(default_project)
        session.commit()
    else:
        message = _(u'a user with this id %d already exists' % user.id)
        request.session.flash(message, 'error')


