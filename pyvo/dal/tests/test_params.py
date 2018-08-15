#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Tests for pyvo.dal.datalink
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from functools import partial
from six.moves.urllib.parse import parse_qsl

from pyvo.dal.adhoc import DatalinkResults
from pyvo.dal.params import find_param_by_keyword, Converter

import pytest

import numpy as np
import astropy.units as u
from astropy.utils.data import get_pkg_data_contents, get_pkg_data_fileobj

get_pkg_data_contents = partial(
    get_pkg_data_contents, package=__package__, encoding='binary')

get_pkg_data_fileobj = partial(
    get_pkg_data_fileobj, package=__package__, encoding='binary')


@pytest.fixture()
def proc(mocker):
    def callback(request, context):
        return get_pkg_data_contents('data/datalink/proc.xml')

    with mocker.register_uri(
        'GET', 'http://example.com/proc', content=callback
    ) as matcher:
        yield matcher


@pytest.fixture()
def proc_units(mocker):
    def callback(request, context):
        data = dict(parse_qsl(request.query))
        if 'band' in data:
            assert data['band'] == (
                '6.000000000000001e-07 8.000000000000001e-06')

        return get_pkg_data_contents('data/datalink/proc.xml')

    with mocker.register_uri(
        'GET', 'http://example.com/proc_units', content=callback
    ) as matcher:
        yield matcher


@pytest.mark.usefixtures('proc')
@pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.W06")
@pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.W48")
@pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.E02")
def test_find_param_by_keyword():
    datalink = DatalinkResults.from_result_url('http://example.com/proc')
    proc = datalink[0]
    input_params = {param.name: param for param in proc.input_params}

    polygon_lower = find_param_by_keyword('polygon', input_params)
    polygon_upper = find_param_by_keyword('POLYGON', input_params)

    circle_lower = find_param_by_keyword('circle', input_params)
    circle_upper = find_param_by_keyword('CIRCLE', input_params)

    assert polygon_lower == polygon_upper
    assert circle_lower == circle_upper


@pytest.mark.usefixtures('proc')
@pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.W06")
@pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.W48")
@pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.E02")
def test_serialize():
    datalink = DatalinkResults.from_result_url('http://example.com/proc')
    proc = datalink[0]
    input_params = {param.name: param for param in proc.input_params}

    polygon_conv = Converter.from_param(
        find_param_by_keyword('polygon', input_params))
    circle_conv = Converter.from_param(
        find_param_by_keyword('circle', input_params))
    scale_conv = Converter.from_param(
        find_param_by_keyword('scale', input_params))
    kind_conv = Converter.from_param(
        find_param_by_keyword('kind', input_params))

    assert polygon_conv.serialize((1, 2, 3)) == "1.0 2.0 3.0"
    assert polygon_conv.serialize(np.array((1, 2, 3))) == "1.0 2.0 3.0"

    assert circle_conv.serialize((1, 2, 3)) == "1.0 2.0 3.0"
    assert circle_conv.serialize(np.array((1, 2, 3))) == "1.0 2.0 3.0"

    assert scale_conv.serialize(1) == "1"
    assert kind_conv.serialize("DATA") == "DATA"


@pytest.mark.usefixtures('proc')
@pytest.mark.usefixtures('proc_units')
def test_units():
    datalink = DatalinkResults.from_result_url('http://example.com/proc')
    proc = datalink[0]

    proc.process(band=(6000*u.Angstrom, 80000*u.Angstrom))