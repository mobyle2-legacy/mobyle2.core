#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from mobyle2.utils import _
from apex import forms
import  wtforms  as w
from wtforms import validators

from sqlalchemy import func

from pyramid.threadlocal import get_current_request

from mobyle2.models import DBSession
from mobyle2.models.auth import self_registration

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
        pass




# vim:set et sts=4 ts=4 tw=80:
