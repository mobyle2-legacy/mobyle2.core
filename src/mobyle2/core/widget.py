#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import colander
from deform import widget,ZPTRendererFactory, schema
import deform
from pkg_resources import resource_filename
from mobyle2.core.utils import _

import demjson as json

deform_templates = resource_filename('deform', 'templates')
mobyle2_templates = resource_filename('mobyle2.core', 'templates/deform')
search_path = (mobyle2_templates, deform_templates)

def renderer_factory(request=None):
    translator = request.translate
    renderer_factory = ZPTRendererFactory(
        search_path=search_path, translator=translator)
    return renderer_factory

class Form(deform.Form):

    def __init__(self, request, *args, **kwargs):
        kwargs['renderer'] = renderer_factory(request)
        deform.Form.__init__(self, *args, **kwargs)
        self.request = request

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


class ChosenSelectWidget(widget.SelectWidget):
    """
    data_url:
        Optionnal ajax url to grab data from
    chosen_opts:
        dict of options JSON serializable to give to chosen constructor
    multiple:
        set multiple html property
    """
    template = 'chosen-select'
    readonly_template = 'readonly/chosen-select'
    chosen_opts = {"allow_single_deselect": True,
                   "no_results_text": _("No results matched..."),}
    width = '200px'
    multiple = False

    def get_multiple(self):
        ret = ''
        if not self.multiple:
            ret = 'false'
        return ret
    def get_chosen_opts(self):
        return json.encode(self.chosen_opts)
    def get_data_url(self):
        return json.encode(getattr(self, 'data_url', None) )

    def __init__(self, data_url, chosen_opts=None, **kw):
        widget.SelectWidget.__init__(self, **kw)
        self.data_url = data_url
        if chosen_opts:
            self.chosen_opts = chosen_opts

# vim:set et sts=4 ts=4 tw=80:
