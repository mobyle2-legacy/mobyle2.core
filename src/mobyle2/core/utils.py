#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

def splitstrip(l):
    return [a.strip()
            for a in l.split()
            if a.strip()] 
