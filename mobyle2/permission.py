#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

from mobyle2.utils import _

manage_portal         = "mobyle2 > manage_portal"
user_add              = "mobyle2 > user_add"
user_edit             = "mobyle2 > user_edit"
user_del              = "mobyle2 > user_del"

group_add             = "mobyle2 > group_add"
group_edit            = "mobyle2 > group_edit"
group_del             = "mobyle2 > group_del"

manage_groups         = "mobyle2 > manage_groups"
manage_roles          = "mobyle2 > manage_roles"

manage_project_groups = "mobyle2 > manage_project_groups"
manage_project_roles  = "mobyle2 > manage_project_roles"

root_project_edit     = "mobyle2 > root_project_edit"
root_project_add      = "mobyle2 > root_project_add"
root_project_view     = "mobyle2 > root_project_view"
root_project_del      = "mobyle2 > root_project_del"

services_view         = "mobyle2 > services_view"

project_view          = "mobyle2 > project_view"
project_add           = "mobyle2 > project_add"
project_edit          = "mobyle2 > project_edit"
project_del           = "mobyle2 > project_del"

service_add           = "mobyle2 > service_add"
service_view          = "mobyle2 > service_view"
service_delete        = "mobyle2 > service_dele"
service_edit          = "mobyle2 > service_edit"

view_service          = "mobyle2 > view_service"
add_service           = "mobyle2 > add_service"
edit_service          = "mobyle2 > edit_service"
del_service           = "mobyle2 > del_service"

notebook_view         = "mobyle2 > notebook_view"
notebook_add          = "mobyle2 > notebook_add"
notebook_edit         = "mobyle2 > notebook_edit"
notebook_del          = "mobyle2 > notebook_del"

job_view              = "mobyle2 > job_view"
job_run               = "mobyle2 > job_run"
job_add               = "mobyle2 > job_add"
job_edit              = "mobyle2 > job_edit"
job_del               = "mobyle2 > job_del"

global_permissions = {
    manage_portal:_("Manage portal"),
    user_add: _("Add an user"),
    user_edit: _("Edit an user"),
    user_del: _("Delete an user"),

    group_add: _("Add a group"),
    group_edit: _("Edit a group"),
    group_del: _("Delete a group"),

    manage_groups: _("Manage groups"),
    manage_roles: _("Manage roles"),

    manage_project_groups: _("Manage group project access"),
    manage_project_roles: _("Manage project roles"),

    root_project_edit: _("Edit the root project"),
    root_project_add: _("Add the root project"),
    root_project_view: _("View the root project"),
    root_project_del: _("Delete the root project"),
    services_view: _("View services"),
}


project_permissions = {
    project_view: _("View a project"),
    project_add:  _("Add a project"),
    project_edit: _("Edit a project"),
    project_del:  _("Delete a project"),
}

service_permissions = {
    service_add:    _("Add a service"),
    service_view:   _("View a service"),
    service_delete: _("Delete a service"),
    service_edit:   _("Edit a service"),
}

notebook_permissions = {
    notebook_view: _("View a notebook"),
    notebook_add:  _("Add a notebook"),
    notebook_edit: _("Edit a notebook"),
    notebook_del:  _("Delete a notebook"),
}

job_permissions = {
    job_view: _("View job"),
    job_run: _("Run a job"),
    job_add: _("Add a job"),
    job_edit: _("Edit a job"),
    job_del: _("Delete a job"),
}
all_permissions = {}
for perms in (global_permissions,
              project_permissions,
              service_permissions,
              job_permissions,
              notebook_permissions):
    all_permissions.update(perms)

