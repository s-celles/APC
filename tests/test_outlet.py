import pytest
from apc.outlet import OutletStatus, Outlet, Outlets
from apc.outlet import OutletsException, OutletStatusParseException, OutletParseException


def test_outlet_status_contructor_with_default_values():
    ols = OutletStatus()
    assert not ols.on
    assert ols.off
    assert not ols.pending

def test_outlet_status_contructor():
    # OFF
    ols = OutletStatus(on=False, pending=False)
    assert not ols.on
    assert ols.off
    assert not ols.pending
    assert str(ols) == 'OFF'

    # ON
    ols = OutletStatus(on=True, pending=False)
    assert ols.on
    assert not ols.off
    assert not ols.pending
    assert str(ols) == 'ON'

    # OFF*
    ols = OutletStatus(on=False, pending=True)
    assert not ols.on
    assert ols.off
    assert ols.pending
    assert str(ols) == 'OFF*'

    # ON*
    ols = OutletStatus(on=True, pending=True)
    assert ols.on
    assert not ols.off
    assert ols.pending
    assert str(ols) == 'ON*'

def test_outlet_status_parse():
    for status in ['OFF', 'ON', 'OFF*', 'ON*']:
        ols = OutletStatus.parse(status)
        assert str(ols) == status
    with pytest.raises(OutletStatusParseException):
        status = 'XYZ'  # this is not an allowed status an exception should be raised
        ols = OutletStatus.parse(status)
        assert str(ols) == status

def test_outlet_contructor():
    ol = Outlet(2, status='OFF', name='MyServer#2')
    assert str(ol) == 'Outlet 2 MyServer#2      OFF'

    ol = Outlet(2, status='OFF*', name='A'*20)
    assert str(ol) == 'Outlet 2 AAAAAAAAAAAAAAA OFF*'  # display name with only 15 characters

def test_outlet_parse():
    row = '2- Outlet 2 MyServer#2      ON*'
    ol = Outlet.parse(row)
    assert ol.id == 2
    assert ol.name == 'MyServer#2'
    assert str(ol.status) == 'ON*'
    assert str(ol) == "Outlet 2 MyServer#2      ON*"

    row = '2- Outlet 2 AAAAAAAAAAAAA   OFF*'
    ol = Outlet.parse(row)
    assert ol.id == 2
    assert ol.name == 'AAAAAAAAAAAAA'
    assert str(ol.status) == 'OFF*'
    assert str(ol) == "Outlet 2 AAAAAAAAAAAAA   OFF*"

    row = '2- AAAAAAAAAAAAA   OFF*'
    ol = Outlet.parse(row)
    assert ol.id == 2
    assert ol.name == 'AAAAAAAAAAAAA'
    assert str(ol.status) == 'OFF*'
    assert str(ol) == "Outlet 2 AAAAAAAAAAAAA   OFF*"

    with pytest.raises(OutletParseException):
        row = 'Xutlet 2 AAAAAAAAAAAAAAA OFF*'  # this is not an allowed status an exception should be raised
        ol = Outlet.parse(row)
        assert str(ol) == row

def test_outlets_collection():
    with pytest.raises(OutletsException):
        ol_collection = Outlets([
            Outlet(1, 'MyServer#1', 'OFF'),
            Outlet(1, 'MyServer#1', 'ON')
        ])

    ol_collection = Outlets([
        Outlet(1, 'MyServer#1', 'OFF'),
        Outlet(2, 'MyServer#2', 'ON'),
        Outlet(3, 'MyServer#3', 'OFF*'),
        Outlet(4, 'MyServer#4', 'ON*'),
        Outlet(5, 'MyServer#5', 'OFF'),
        Outlet(6, 'MyServer#6', 'ON'),
        Outlet(7, 'MyServer#7', 'OFF*'),
        Outlet(8, 'MyServer#8', 'ON*'),
    ])
    assert str(ol_collection) == """Outlet 1 MyServer#1      OFF
Outlet 2 MyServer#2      ON
Outlet 3 MyServer#3      OFF*
Outlet 4 MyServer#4      ON*
Outlet 5 MyServer#5      OFF
Outlet 6 MyServer#6      ON
Outlet 7 MyServer#7      OFF*
Outlet 8 MyServer#8      ON*"""

    ol = ol_collection[4]
    assert ol.id == 4
    assert ol.name == 'MyServer#4'
    assert str(ol.status) == 'ON*'

    assert len(ol_collection) == 8

    for i, ol in enumerate(ol_collection, 1):
        assert ol.id == i
