#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

import colander
from deform import widget,ZPTRendererFactory, schema
import deform
from pkg_resources import resource_filename
from mobyle2.core.utils import _

import demjson as json

from colander import null

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
    repeat_columns = 5

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


class MultipleChosenSelectWidget(widget.SelectWidget):
    """
    data_url:
        Optionnal ajax url to grab data from
    chosen_opts:
        dict of options JSON serializable to give to chosen constructor
    multiple:
        set multiple html property
    """
    size=0
    template = 'chosen-select'
    readonly_template = 'readonly/chosen-select'
    chosen_opts = {"no_results_text": _("No results matched..."),}
    width = '400px'
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

    def get_values(self, cstruct):
        data, keys, cdata = [], [], None
        if cstruct:
            exec 'cdata=%s' % cstruct
        if not isinstance(cdata, list) or isinstance(cdata, tuple):
            cdata = [cdata]
        if cdata:
            for value in cdata:
                k, s = '', ''
                if isinstance(value, basestring):
                    k, s = value, value
                elif isinstance(value, list) or isinstance(value, tuple):
                    k, s = value[0], value[1]
                if not k in keys:
                    data.append(('selected', k, s))
                    keys.append(k)
        for value in getattr(self, 'values', []):
            if isinstance(value, basestring):
                k, s = value, value
            elif isinstance(value, list) or isinstance(value, tuple):
                k, s = value[0], value[1]
            if not k in keys:
                data.append(('', k, s))
                keys.append(k)
        return data

    def __init__(self, data_url, chosen_opts=None, width=width, size=size, **kw):
        self.size = size
        self.width=width
        widget.SelectWidget.__init__(self, **kw)
        self.data_url = data_url
        if chosen_opts:
            self.chosen_opts = chosen_opts
        if self.size == 1:
            self.chosen_opts["allow_single_deselect"] = True
            self.multiple = False
        else:
            self.multiple = True

    def deserialize(self, field, pstruct):
        cstruct = widget.SelectWidget.deserialize(self, field, pstruct)
        if not isinstance(cstruct, tuple) and not isinstance(cstruct, list):
            cstruct = [cstruct]
        for i, item in enumerate(cstruct[:]):
            if isinstance(item, basestring):
                cstruct[i] = (item, '')

        def filtering(item):
            if item:
                if isinstance(item, list) or isinstance(item, tuple):
                    if item[0]:
                        return True
                else:
                    return True
        cstruct = filter(filtering, cstruct)
        return cstruct

class SingleChosenSelectWidget(MultipleChosenSelectWidget):
    def __init__(self, data_url, width=MultipleChosenSelectWidget.width, chosen_opts=None, **kw):
        size = 1
        MultipleChosenSelectWidget.__init__(self, data_url, chosen_opts, width, size, **kw)

ChosenSelectWidget = MultipleChosenSelectWidget

# vim:set et sts=4 ts=4 tw=80:
