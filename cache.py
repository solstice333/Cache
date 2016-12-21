#!/usr/bin/env python3.5
from collections import OrderedDict
from custom_exceptions import *

class Cache(OrderedDict):
    def __init__(self, capacity=10, init_values=None):
        self.capacity = capacity
        super().__init__(init_values or {})

    def __setitem__(self, key, val):
        if (len(self) >= self.capacity):
            raise MaxCapacityError()
        super().__setitem__(key, val)

    def __str__(self):
        return super().__str__()