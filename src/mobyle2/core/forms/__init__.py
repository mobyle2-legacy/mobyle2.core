#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from mobyle2.core.utils import _
from apex import forms
import  wtforms  as w
from wtforms import validators

from sqlalchemy import func

from pyramid.threadlocal import get_current_request

from mobyle2.core.models import DBSession
from mobyle2.core.models.auth import self_registration

from apex.models import AuthUser

def translate(string):
    return get_current_request().translate(string)

class OnlyOneMail(object):
    """
    Validates that the mail is unique in authuser table
    """

    def __call__(self, form, field):
        session = DBSession()
        if field.data and isinstance(field.data, basestring):
            data = field.data.strip().lower()
            users = session.query(
                AuthUser).filter(
                    func.lower(AuthUser.email) == data).all()
            if len(users):
                self.message = field.gettext(
                    _(u'This email already exists, '
                      'please choose another one or '
                      'retrieve your identity.'))
                field.errors[:] = []
                raise validators.StopValidation(self.message)

class RegisterForm(forms.RegisterForm):
    email = w.TextField(translate('Email Address'),
                        [validators.Required(),
                         validators.Email(),
                         OnlyOneMail()])

    def clean(self):
        """Aditionnal validations.
           - validate that self_registration is on
        """
        errors = []
        if not self_registration():
            errors.append(
                _(u'Self registration is turned off '
                  'by the administrator on this portal.'))
        return errors

    def after_signup(self, user, **kwargs):
        """
        Create a default project.
        """
        from mobyle2.core.models import DBSession as session
        from mobyle2.core.models.user import User
        if not session.query(User).filter_by(id=user.id).all():
            from mobyle2.core.models.project import Project
            newuser = User(user.id, 'a')
            session.add(newuser)
            session.commit()
            default_project = Project('Default project of %s' % user.username,
                                      'Default project created on sign in', newuser)
            session.add(default_project)
            session.commit()
        else:
            self.message = _(u'a user with this id %d already exists' % user.id)




# vim:set et sts=4 ts=4 tw=80:
