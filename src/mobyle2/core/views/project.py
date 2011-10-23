#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mobyle2.core.views import Base

class List(Base):
    template ='project/project_list.mako'
class View(Base):
    template ='project/project_view.mako'
class Edit(Base):
    template ='project/project_edit.mako'

# vim:set et sts=4 ts=4 tw=80:
