# coding: utf-8
"""
Constants used across the app.
"""
from __future__ import absolute_import, print_function, unicode_literals

# Some backends give more infos than others. Here is the precedence we want to
# use. First is most important one, last is the one that will always be
# considered as less trustable if two backends have similar info about a
# housing.
BACKENDS_BY_PRECEDENCE = [
    "foncia",
    "seloger",
    "pap",
    "leboncoin",
    "explorimmo",
    "logicimmo"
]
