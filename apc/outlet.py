#!/usr/bin/env python

from collections import OrderedDict
import re
APC_OUTLET_STATUS_PATTERN = re.compile('(OFF|ON)(\*?)')
APC_OUTLET_ROW_PATTERN = re.compile('Outlet (\d) (.*) (OFF\*?|ON\*?)')
APC_OUTLET_ROW_PATTERN2 = re.compile('(\d)- (.*) (OFF\*?|ON\*?)')


class OutletStatusParseException(Exception):
    pass


class OutletStatus:
    def __init__(self, on=False, pending=False):
        self.on = on
        self.pending = pending

    @property
    def off(self):
        return not self.on

    def __str__(self):
        if self.on:
            s = "ON"
        else:
            s = "OFF"
        if self.pending:
            s = s + "*"
        return s

    @classmethod
    def parse(cls, s):
        s = s.upper()
        match = APC_OUTLET_STATUS_PATTERN.search(s)
        if not match:
            raise OutletStatusParseException('Could not parse APC outlet status')
        s_on_off, s_pending = match.groups()
        if s_on_off == "ON":
            on = True
        else:  # "OFF"
            on = False
        if s_pending == "*":
            pending = True
        else:
            pending = False
        return cls(on, pending)


class OutletParseException(Exception):
    pass


class Outlet:
    def __init__(self, id, name='', status='OFF'):
        self.id = id
        self.name = name
        self.status = OutletStatus.parse(status)

    def __str__(self):
        n = 15  # maximum number of characters to display
        name = self.name[0:n].ljust(n)
        return "Outlet %d %s %s" % (self.id, name, self.status)

    @classmethod
    def parse(cls, s):
        # Two forms of rows can be parsed, either:
        # 1- OUTLETNAME    ON"
        # or
        # Outlet 1 OUTLETNAME    ON"

        # try first form, without the 3 first characters
        match = APC_OUTLET_ROW_PATTERN.search(s[3:])
        # if fails, try second
        if not match:
            match = APC_OUTLET_ROW_PATTERN2.search(s)
        # fail if neither patterns match
        if not match:
            raise OutletParseException('Could not parse APC outlet status')
        s_id, s_name, s_status = match.groups()
        id = int(s_id)
        name = s_name.strip()
        return cls(id, name, s_status)


class OutletsException(Exception):
    pass


class Outlets:
    def __init__(self, lst_outlets):
        self._d = OrderedDict()
        for outlet in lst_outlets:
            if outlet.id in self._d:
                raise OutletsException("Outlet %d ever exists in this collection"  % outlet.id)
            self._d[outlet.id] = outlet

    def __str__(self):
        return "\n".join(map(str, self._d.values()))

    def __getitem__(self, key):
        return self._d[key]

    def __len__(self):
        return len(self._d)

    def __iter__(self):
        return iter(self._d.values())
