#!/usr/bin/env python3.5
from collections import OrderedDict
from collections.abc import MutableMapping
import shelve


class CacheMiss(Exception):
   def __str__(self):
      return "Cache miss"


class NoBStoreError(Exception):
   def __str__(self):
      return "No backing store exists"


class BStoreClosedError(Exception):
   def __str__(self):
      return "Backing store not open"


class BackingStore(MutableMapping):
   __marker = object()

   def _raise_on_bstore_closed(self):
      if self.closed():
         raise BStoreClosedError

   def _trim_to_capacity(self):
      if self._db is not None:
         while len(self._db) > self._capacity:
            self._db.popitem()

   def _notify_modify_dirty_above_for(self, key):
      mem = self._upper_mem
      while mem is not None:
         mem._modify_key = key
         mem = mem._upper_mem

   def __init__(self, capacity=10, dbname='bstore'):
      if capacity < 1:
         raise ValueError("capacity must be greater than 0")
      self._capacity = capacity
      self._dbname = dbname
      self._db = None
      self._nondirty_map = {}
      self._upper_mem = None

   @property
   def capacity(self):
      return self._capacity

   @capacity.setter
   def capacity(self, new_cap):
      self._capacity = new_cap
      self._trim_to_capacity()

   @property
   def dbname(self):
      return self._dbname

   def open(self):
      self._db = shelve.open(self._dbname)
      self._trim_to_capacity()

   def close(self):
      if self._db is not None:
         self._db.close()
         self._db = None

   def closed(self):
      return self._db is None

   def __getitem__(self, key):
      self._raise_on_bstore_closed()
      return self._db[key]

   def __setitem__(self, key, value):
      self._raise_on_bstore_closed()
      while len(self._db) >= self._capacity:
         self.popitem()
      self._db[key] = value

   def __delitem__(self, key):
      self._raise_on_bstore_closed()
      del self._db[key]

   def __iter__(self):
      self._raise_on_bstore_closed()
      return iter(self._db)

   def __len__(self):
      self._raise_on_bstore_closed()
      return len(self._db)

   def __contains__(self, item):
      self._raise_on_bstore_closed()
      return item in self._db

   def keys(self):
      self._raise_on_bstore_closed()
      return list(self._db.keys())

   def items(self):
      self._raise_on_bstore_closed()
      return list(self._db.items())

   def values(self):
      self._raise_on_bstore_closed()
      return list(self._db.values())

   def get(self, key, default=None):
      self._raise_on_bstore_closed()
      return self._db.get(key, default)

   def __eq__(self, other):
      return self._db == other and self.capacity == other._capacity

   def __ne__(self, other):
      return self._db != other

   def pop(self, key, default=__marker):
      self._raise_on_bstore_closed()
      return self._db.pop(key) if default == BackingStore.__marker \
         else self._db.pop(key, default)

   def popitem(self):
      self._raise_on_bstore_closed()
      for k in self.keys():
         if k not in self._nondirty_map:
            return k, self._db.pop(k)
      item = self._db.popitem()
      self._notify_modify_dirty_above_for(item[0])
      return item

   def clear(self):
      self._raise_on_bstore_closed()
      self._db.clear()

   def update(self, other):
      self._raise_on_bstore_closed()
      self._db.update(other)

   def setdefault(self, key, default=None):
      self._raise_on_bstore_closed()
      return self._db.setdefault(key, default)

   def __str__(self):
      ldump = []
      try:
         for k, v in self.items():
            ldump.append((k, v))
         ldump.sort(key=lambda t: t[0])
         ldump = [str(i) for i in ldump]
         return "BackingStore: [{}]".format(", ".join(ldump))
      except BStoreClosedError:
         return "BackingStore: closed"

   def __enter__(self):
      self.open()
      return self

   def __exit__(self, exc_type, exc_val, exc_tb):
      self.close()
      return False


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
         return not (self == other)

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

   def _popitem(self, last=True, unwrap=False):
      entry = self._cache.popitem(last)
      if unwrap:
         return entry[0], entry[1].val
      return entry

   def _recurs_pop_unless_from_bs(self, key):
      try:
         return self._pop(key).val, False
      except KeyError:
         try:
            return self.lower_mem._recurs_pop_unless_from_bs(key)
         except AttributeError:
            if self.lower_mem is None:
               raise CacheMiss
            try:
               return self.lower_mem[key], True
            except KeyError:
               raise CacheMiss

   def _modify_dirty_if_notified(self):
      if self._modify_key is not None:
         try:
            item = self._cache[self._modify_key]
            self._cache[self._modify_key] = Cache._Val(True, item.val)
            self._modify_key = None
         except KeyError:
            pass

   def _setitem(self, key, val, dirty=True):
      try:
         self._cache.pop(key)
      except KeyError:
         while (len(self._cache) >= self._capacity):
            item = self._popitem(False)
            try:
               if self._lower_mem is not None:
                  self._lower_mem._setitem(item[0], item[1].val, item[1].dirty)
            except AttributeError:
               if item[1].dirty:
                  self._lower_mem[item[0]] = item[1].val
      self._cache[key] = Cache._Val(dirty, val)
      self._modify_dirty_if_notified()

   def _send_bs_nondirties(self, *more):
      if self._is_lowest_mem_bstore():
         bs = self._get_lowest_mem()
         nondirty_map = dict([*more])

         mem = self
         while mem is not bs:
            nondirty_map.update(
               {k: v.val for k, v in mem._items() if not v.dirty})
            mem = mem.lower_mem
         bs._nondirty_map = nondirty_map

   def _get_lowest_mem(self):
      mem = self
      try:
         while mem.lower_mem is not None:
            mem = mem.lower_mem
      except AttributeError:
         pass
      return mem

   def _is_lowest_mem_bstore(self):
      return isinstance(self._get_lowest_mem(), BackingStore)

   def __init__(self, capacity=10, init_values=None, lower_mem=None):
      if capacity < 1:
         raise ValueError("capacity must be greater than 0")
      self._capacity = capacity
      self._lower_mem = lower_mem
      self._upper_mem = None
      self._modify_key = None

      if not (lower_mem is None or isinstance(lower_mem, Cache) or
                 isinstance(lower_mem, BackingStore)):
         raise TypeError(
            "lower_mem must be None or of type Cache or BackingStore")

      if self._lower_mem is not None:
         self._lower_mem._upper_mem = self

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

   @property
   def lower_mem(self):
      return self._lower_mem

   def __getitem__(self, key):
      item, from_bstore = self._recurs_pop_unless_from_bs(key)
      dirty = False if from_bstore else True
      self._send_bs_nondirties((key, item))
      self._setitem(key, item, dirty)
      return item

   def __setitem__(self, key, val):
      args = []
      try:
         item, from_bstore = self._recurs_pop_unless_from_bs(key)
         dirty = False if from_bstore else True
         args.append((key, item))
      except CacheMiss:
         pass
      self._send_bs_nondirties(*args)
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
      return list(self._cache.keys())

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
             self._capacity == other._capacity and \
             self._lower_mem == other._lower_mem

   def __ne__(self, other):
      return not (self == other)

   def pop(self, key, default=__marker):
      return self._pop(key, default, True)

   def popitem(self, last=True):
      return self._popitem(last, True)

   def clear(self):
      self._cache.clear()

   def update(self, other):
      self._cache.update(other._items())

   def setdefault(self, key, default=None):
      try:
         return self[key]
      except CacheMiss:
         self[key] = default
         return default

   def open_bstore(self):
      if not self._is_lowest_mem_bstore():
         raise NoBStoreError
      bs = self._get_lowest_mem()
      bs.open()

   def close_bstore(self):
      if self._is_lowest_mem_bstore():
         bs = self._get_lowest_mem()
         bs.close()

   def bstore_closed(self):
      if self._is_lowest_mem_bstore():
         bs = self._get_lowest_mem()
         return bs.closed()
      else:
         return True

   def __enter__(self):
      self.open_bstore()
      return self

   def __exit__(self, exc_type, exc_val, exc_tb):
      self.close_bstore()
      return False
