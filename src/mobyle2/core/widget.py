#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import colander
from deform import widget,ZPTRendererFactory, schema
from pkg_resources import resource_filename

deform_templates = resource_filename('deform', 'templates')
mobyle2_templates = resource_filename('mobyle2.core', 'templates/deform')
search_path = (mobyle2_templates, deform_templates)

def renderer_factory(request=None):
    translator = request.translate
    renderer_factory = ZPTRendererFactory(
        search_path=search_path, translator=translator)
    return renderer_factory

class TableWidget(widget.MappingWidget):
    """"""
    template = 'table'
    item_template = 'table_item'
    headers = []

class LabelledTrWidget(widget.MappingWidget):
    template = 'tmapping'
    readonly_template = 'readonly/tmapping' 
    item_template = 'tmapping_item'
    readonly_item_template = 'readonly/tmapping_item'   
    display_title = True

class TrWidget(LabelledTrWidget):
    display_title = False

class TableBaseNode(colander.SchemaNode):
    _widget_class = TableWidget
    def __init__(self, *args, **kwargs):
        colander.SchemaNode.__init__(self, *args, **kwargs)
        self.widget = self._widget_class()

class TableNode(TableBaseNode):
    _widget_class = TableWidget

class TrNode(TableBaseNode):
    _widget_class = TrWidget

# vim:set et sts=4 ts=4 tw=80:
