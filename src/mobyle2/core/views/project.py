#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyramid.renderers   import render_to_response
from mobyle2.core.config import template_path as t
def list(request):
    import pdb;pdb.set_trace()  ## Breakpoint ##
    return render_to_response('%s/project_list.pt' % t, {}, request)
def view(request):
    import pdb;pdb.set_trace()  ## Breakpoint ##
    return render_to_response('%s/project_view.pt' % t, {}, request) 
def edit(request):
    import pdb;pdb.set_trace()  ## Breakpoint ##
    return render_to_response('%s/project_edit.pt' % t, {}, request)  
# vim:set et sts=4 ts=4 tw=80:
