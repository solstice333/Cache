#!/usr/bin/env python3.5
from collections import OrderedDict
from custom_exceptions import *

class Cache():
    def __init__(self, capacity=10, init_values=None):
        self.capacity = capacity
        self._page_map = OrderedDict(init_values or {})

    def __getitem__(self, key):
        return self._page_map[key]

    def __setitem__(self, key, val):
        if (len(self) >= self.capacity):
            raise MaxCapacityError()
        self._page_map[key] = val

    def __len__(self):
        return len(self._page_map)

