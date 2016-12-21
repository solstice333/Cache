#!/usr/bin/env python3.5
from collections import OrderedDict
from collections.abc import MutableMapping

class Cache(MutableMapping):
    __marker = object()

    def __init__(self, capacity=10, init_values=None):
        self._capacity = capacity
        self._cache = OrderedDict(init_values or {})

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, new_cap):
        self._capacity = new_cap
        trim = len(self._cache) - self._capacity
        if (trim > 0):
            for i in range(trim):
                self.popitem(last=True)

    def __getitem__(self, key):
        try:
            val = self._cache.pop(key)
        except KeyError:
            return None

        self._cache[key] = val
        return val

    def __setitem__(self, key, val):
        try:
            self._cache.pop(key)
        except KeyError:
            if (len(self._cache) >= self._capacity):
                self._cache.popitem(last=False)
        self._cache[key] = val

    def __delitem__(self, key):
        del self._cache[key]

    def __len__(self):
        return len(self._cache)

    def items(self):
        return self._cache.items()

    def __iter__(self):
        return iter(self._cache)

    def keys(self):
        return self._cache.keys()

    def values(self):
        return self._cache.values()

    def __str__(self):
        return "Cache: {}".format(self._cache)

    def __contains__(self, item):
        return item in self._cache

    def get(self, key, default=None):
        return self._cache.get(key, default)

    def __eq__(self, other):
        return self._cache == other._cache and \
               self._capacity == other._capacity

    def __ne__(self, other):
        return not self.__eq__(other)

    def pop(self, key, default=__marker):
        return self._cache.pop(key) if default == Cache.__marker \
            else self._cache.pop(key, default)

    def popitem(self, last=True):
        return self._cache.popitem(last)

    def clear(self):
        self._cache.clear()

    def update(self, other):
        self._cache.update(other)
