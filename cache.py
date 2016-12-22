#!/usr/bin/env python3.5
from collections import OrderedDict
from collections.abc import MutableMapping

class CacheMiss(Exception):
   def __str__(self):
      return "Cache miss"

class Cache(MutableMapping):
   __marker = object()

   class _Val():
      def __init__(self, dirty, val):
         self.dirty = bool(dirty)
         self.val = val

      def to_tuple(self):
         return self.dirty, self.val

      def __eq__(self, other):
         return self.dirty == other.dirty and self.val == other.val

      def __ne__(self, other):
         return self.__eq__(other)

      def __str__(self):
         return "({}, {})".format(self.dirty, self.val)

   def _items(self):
      return [(k, v) for k, v in self._cache.items()]

   def _values(self):
      return self._cache.values()

   def _pop(self, key, default=__marker, unwrap=False):
      item = self._cache.pop(key) if default == Cache.__marker \
         else self._cache.pop(key, default)
      try:
         return item.val if unwrap else item
      except AttributeError:
         return item

   def _recurs_pop(self, key):
      try:
         return self._pop(key)
      except KeyError:
         try:
            return self._lower_mem._recurs_pop(key)
         except AttributeError:
            raise CacheMiss

   def __init__(self, capacity=10, init_values=None, lower_mem=None):
      self._capacity = capacity
      self._lower_mem = lower_mem

      try:
         if isinstance(init_values, list):
            new_od = []
            for pair in init_values:
               entry = pair[0], Cache._Val(True, pair[1])
               new_od.append(entry)
         elif isinstance(init_values, dict):
            new_od = {}
            for k, v in init_values.items():
               new_od[k] = Cache._Val(True, v)
         else:
            raise TypeError
      except TypeError:
         if init_values is None:
            new_od = {}
         else:
            raise TypeError('init_values needs to be a list or dict')

      self._cache = OrderedDict(new_od)

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
      item = self._recurs_pop(key)
      self._setitem(key, item.val, item.dirty)
      return item.val

   def _setitem(self, key, val, dirty=True):
      try:
         self._cache.pop(key)
      except KeyError:
         while (len(self._cache) >= self._capacity):
            # TODO: demote down to lower mem. if no lower mem, remove
            self._cache.popitem(last=False)
      self._cache[key] = Cache._Val(dirty, val)

   def __setitem__(self, key, val):
      self._setitem(key, val)

   def __delitem__(self, key):
      del self._cache[key]

   def __len__(self):
      return len(self._cache)

   def items(self):
      return [(k, v.val) for k, v in self._cache.items()]

   def __iter__(self):
      return iter(self._cache)

   def keys(self):
      return self._cache.keys()

   def values(self):
      return [v.val for v in self._cache.values()]

   def __str__(self):
      return "Cache: [" + \
             ", ".join(
                ["({}, {})".format(
                   k, v) for k, v in self._items()]) + \
             "]"

   def __contains__(self, item):
      return item in self._cache

   def get(self, key, default=None):
      got = self._cache.get(key, default)
      return got.val if got is not default else got

   def __eq__(self, other):
      return self._cache == other._cache and \
             self._capacity == other._capacity

   def __ne__(self, other):
      return not self.__eq__(other)

   def pop(self, key, default=__marker):
      return self._pop(key, default, True)

   def popitem(self, last=True):
      entry = self._cache.popitem(last)
      return entry[0], entry[1].val

   def clear(self):
      self._cache.clear()

   def update(self, other):
      self._cache.update(other._items())
