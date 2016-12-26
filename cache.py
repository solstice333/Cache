#!/usr/bin/env python3.5
from collections import OrderedDict
from collections.abc import MutableMapping
import shelve


class CacheMiss(Exception):
   """exception for a cache miss"""

   def __str__(self):
      """return string representation of CacheMiss"""
      return "Cache miss"


class NoBStoreError(Exception):
   """exception for no backing store linked to the cache"""

   def __str__(self):
      """return string representation of NoBStoreError"""
      return "No backing store exists"


class BStoreClosedError(Exception):
   """exception for when a backing store hasn't been opened yet"""

   def __str__(self):
      """return string representation of BStoreClosedError"""
      return "Backing store not open"


class BackingStore(MutableMapping):
   """Backing Store class. Link this to a Cache object

   This class represents a backing store which is the lowest storage to
   write to after all levels of caches has missed. It is considered
   persistent non-volatile storage. This class implements the
   collections.abc.MutableMapping interface which acts as a wrapper on top
   of shelve.
   """

   __marker = object()

   def _raise_on_bstore_closed(self):
      # if the backing store is closed, raise a BStoreClosedError
      if self.closed():
         raise BStoreClosedError

   def _trim_to_capacity(self):
      # trim down the contents in the backing store until equal to the
      # maximum capacity. Data is removed randomly.
      if self._db is not None:
         while len(self._db) > self._capacity:
            self._db.popitem()

   def _notify_modify_dirty_above_for(self, key):
      # notify all caches above to look for an entry with key |key|
      #
      # If no cache exists, this is a no-op.
      #
      # Args:
      #    key: string representing the key to look for
      mem = self._upper_mem
      while mem is not None:
         mem._modify_key = key
         mem = mem._upper_mem

   def __init__(self, capacity=10, dbname='bstore'):
      """BackingStore ctor

      Instantiate a BackingStore object with a maximum capacity of
      |capacity|, and writes data to a file named "|dbname|.db".

      Args:
         capacity: integer specifying the maximum capacity the database
            can hold. Default is 10.
         dbname: string representing the name of the database/store.
            Default is 'bstore'
      """
      if capacity < 1:
         raise ValueError("capacity must be greater than 0")
      self._capacity = capacity
      self._dbname = dbname
      self._db = None
      self._nondirty_map = {}
      self._upper_mem = None

   @property
   def capacity(self):
      """get/set capacity of store

      On setting, if the backing store is open and the length of the store
      contents is greater than the capacity, the backing store contents is
      trimmed down to the new capacity. Data is removed randomly.

      Args:
         new_cap: int specifying new capacity

      Returns:
         current capacity
      """
      return self._capacity

   @capacity.setter
   def capacity(self, new_cap):
      self._capacity = new_cap
      self._trim_to_capacity()

   @property
   def dbname(self):
      """get name of database/store

      Returns:
         name of store
      """
      return self._dbname

   def open(self):
      """open the backing store i/o stream

      On opening, if the shelve content length is too large, it is
      reduced down to the maximum capacity. Data is removed randomly.
      """
      self._db = shelve.open(self._dbname)
      self._trim_to_capacity()

   def close(self):
      """close the backing store i/o stream"""
      if self._db is not None:
         self._db.close()
         self._db = None

   def closed(self):
      """return True if backing store is closed; False otherwise"""
      return self._db is None

   def __getitem__(self, key):
      """obj[key]

      get data from backing store

      Args:
         key: string representing the key to look for

      Returns:
         The data associated with |key|

      Raises:
         BStoreClosedError: backing store is closed
         KeyError: |key| doesn't exist
      """
      self._raise_on_bstore_closed()
      return self._db[key]

   def __setitem__(self, key, value):
      """obj[key] = value

      set data in backing store

      Args:
         key: string representing the key to associate |value| with
         value: any data bound to |key|

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      while len(self._db) >= self._capacity:
         self.popitem()
      self._db[key] = value

   def __delitem__(self, key):
      """del obj[key]

      delete data from backing store

      Args:
         key: string representing key

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      del self._db[key]

   def __iter__(self):
      """return an iterator over the keys in the backing store

      Returns:
         iterator over the keys in the backing store

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return iter(self._db)

   def __len__(self):
      """return the number of itmes in the backing store

      Returns:
         number of items in the backing store

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return len(self._db)

   def __contains__(self, key):
      """|key| in obj

      return True if backing store has key; False otherwise

      Args:
         key: string representing the key

      Returns:
         True if |key| is in backing store; False otherwise

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return key in self._db

   def keys(self):
      """return a list of the keys in the backing store

      Returns:
         a list of all the keys in the backing store

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return list(self._db.keys())

   def items(self):
      """return a list of (key, value) pairs contained in the backing store

      Returns:
         a list of (key, value) pairs contained in the backing store

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return list(self._db.items())

   def values(self):
      """return a list of the values in the backing store

      Returns:
         a list of values contained in the backing store

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return list(self._db.values())

   def get(self, key, default=None):
      """return the value for |key| if |key| is in the store

      Args:
         key: string representing the key

      Returns:
         value for |key|

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return self._db.get(key, default)

   def __eq__(self, other):
      """return True if equal; False otherwise

      Equal if |other| store contents have the same (key, value) pairs
      and capacity is the same as self.

      Args:
         other: another BackingStore instance

      Returns:
         True if equal; False otherwise
      """
      return self._db == other._db and self._capacity == other._capacity

   def __ne__(self, other):
      """return True if not equal; False otherwise

      Not equal if |other| store contents have different (key, value)
      pairs or capacity is different from self

      Args:
         other: another BackingStore instance

      Returns:
         True if not equal; False otherwise
      """
      return not (self == other)

   def pop(self, key, default=__marker):
      """Remove |key| and return its value if exists in store

      If |key| is in the store, return the value of |key|; otherwise
      return |default|.

      Args:
         key: string representing the key
         default: any data type representing the default return value
            if |key| is not in store. If |default| is not given, a
            KeyError is raised.

      Returns:
         the value associated to |key|, else |default|.

      Raises:
         KeyError: |key| is not in store
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return self._db.pop(key) if default == BackingStore.__marker \
         else self._db.pop(key, default)

   def popitem(self):
      """Remove and return a (key, value) pair from store

      First, check to see if a key that exists in the store is a key
      who's dirty value in the upper caches is False. If it is, then
      remove that (key, value) pair and return it. Otherwise, remove
      an arbitrary (key, value) pair and return it. The caches above
      are notified of the removed (key, value) pair so that they
      can automatically synchronize the dirty value if needed. That is,
      if a (key, value) pair is removed whose key is in the cache and
      its value isn't dirty, it will be modified to be dirty so it
      can be written back to the store.

      Returns:
         the (key, value) pair removed from the store

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      for k in self.keys():
         if k not in self._nondirty_map:
            return k, self._db.pop(k)
      item = self._db.popitem()
      self._notify_modify_dirty_above_for(item[0])
      return item

   def clear(self):
      """remove all (key, value) pairs from the store

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      self._db.clear()

   def update(self, other):
      """updates the store with (key, value) pairs from another store

      Update the store with (key, value) pairs from the |other| store;
      Existing keys are overwritten.

      Args:
         other: another BackingStore instance

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      self._db.update(other)

   def setdefault(self, key, default=None):
      """return key's value if in store, otherwise insert key

      If |key| is in store, return its value, otherwise insert key
      with a value of |default|.

      Args:
         key: string representing the key
         default: the value to insert if |key| doesn't exist in store.
            Defaults to None.

      Raises:
         BStoreClosedError: backing store is closed
      """
      self._raise_on_bstore_closed()
      return self._db.setdefault(key, default)

   def __str__(self):
      """return a string representation of the backing store

      A string representation of the backing store is all the
      (key, value) pairs sorted by key and listed out. If
      backing store is closed, prints out "BackingStore: closed".

      Returns:
         string representation of the backing store
      """
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
      """Open the backing store and return self using the with statement

      Returns:
         self
      """
      self.open()
      return self

   def __exit__(self, exc_type, exc_val, exc_tb):
      """Closes the backing store

      Raises:
         any exception raised from within the runtime context
      """
      self.close()
      return False


class Cache(MutableMapping):
   """Cache class. Cache and BackingStore objects can be linked to this

   Represents a cache that adheres to an LRU replacement policy,
   write-back, and write allocate policy. If a backing store is linked
   downstream, the dirty values in the (key, value) pairs contained
   in the upper caches are updated accordingly. That is, if a
   (key, value) pair is removed from the backing store whose
   key in the upper cache is marked as non-dirty, it is then marked
   as dirty.
   """

   __marker = object()

   class _Val():
      # Represents a wrapper object for a value in cache
      #
      # Binds a dirty bool to a value.

      def __init__(self, dirty, val):
         # instantiate a _Val object
         #
         # Args:
         #     dirty: True if |val| should be written back to store;
         #        False otherwise
         #     val: any data type to be stored in the cache
         #
         self.dirty = bool(dirty)
         self.val = val

      def to_tuple(self):
         # return a _Val as a (dirty, val) pair
         return self.dirty, self.val

      def __eq__(self, other):
         # return True if self is equal to |other|; False otherwise
         #
         # Equal is if dirty flag and val in self is equal to other's
         # dirty flag and val.
         #
         # Args:
         #     other: another _Val object
         #
         # Returns:
         #     True if self is equal to |other|; False otherwise
         return self.dirty == other.dirty and self.val == other.val

      def __ne__(self, other):
         # return True if self is not equal to |other|; False otherwise
         #
         # Not equal if dirty flag or val in self differs from other's
         # dirty flag and val
         #
         # Args:
         #     other: another _Val object
         #
         # Returns:
         #     True if self is not equal |other|; False otherwise
         return not (self == other)

      def __str__(self):
         # return string representation of a _Val object
         return "({}, {})".format(self.dirty, self.val)

   def _items(self):
      # return a list of items in the self cache. Items are unwrapped
      #
      # Unwrapped means that they are wrapped as a _Val object
      #
      # Returns:
      #     a list of _Val objects. That is, each item is a
      #     (key, _Val) pair
      return [(k, v) for k, v in self._cache.items()]

   def _values(self):
      # return a list of values from the self cache unwrapped
      #
      # Unwrapped means that they are wrapped as a _Val object
      #
      # Returns:
      #     a list of cache values of type _Val
      return list(self._cache.values())

   def _pop(self, key, default=__marker, unwrap=False):
      # removes key from self cache and returns it
      #
      # If |key| exists in cache, remove it and return its value; otherwise
      # return |default|. If |default| isn't specified, KeyError is raised.
      #
      # Args:
      #     key: string representing the key
      #     default: any data to return if
      #        |key| not found
      #     unwrap: if True, unwrap the _Val object and return just the
      #        value; otherwise return the _Val object containing the
      #        (dirty, value) pair
      # Raises:
      #     KeyError: |key| doesn't exist and |default| isn't specified
      item = self._cache.pop(key) if default == Cache.__marker \
         else self._cache.pop(key, default)
      try:
         return item.val if unwrap else item
      except AttributeError:
         return item

   def _popitem(self, last=True, unwrap=False):
      # removes an item from the cache and returns it
      #
      # The item returned is a (key, value) pair
      #
      # Args:
      #     last: if True, returns the last item; otherwise return the
      #        first
      #     unwrap: if True, unwrap the _Val object and return the
      #        value, else return the _Val (dirty, value) pair
      #
      # Returns:
      #     an item, (key, value) pair, from the cache. If unwrap is
      #     True, (key, value) is returned where value is the raw
      #     data originally put in. If unwrap is False, (key, value)
      #     is returned where value is a _Val object representing
      #     a (dirty, value) pair, thus (key, (dirty, value)) is
      #     returned.
      entry = self._cache.popitem(last)
      if unwrap:
         return entry[0], entry[1].val
      return entry

   def _recurs_pop_unless_from_bs(self, key):
      # pop |key| from the cache
      #
      # If cache miss, recursively check the cache/store below self.
      # If |key| is found in a cache, remove the (key, value) pair
      # and return value. If |key| is found in the store, get the
      # (key, value) without removing it, and return value.
      #
      # Args:
      #     key: string representing the key
      #
      # Returns:
      #     value of key
      #
      # Raises:
      #     CacheMiss: the key doesn't exist in the cache or backing
      #        store
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
      # modify the dirty bool of a value in the cache
      #
      # the dirty bool changed is associated to the key specified
      # by the backing store if exists. If no backing store exists
      # this a no-op.
      if self._modify_key is not None:
         try:
            item = self._cache[self._modify_key]
            self._cache[self._modify_key] = Cache._Val(True, item.val)
            self._modify_key = None
         except KeyError:
            pass

   def _setitem(self, key, val, dirty=True):
      # sets item in cache
      #
      # the least recently used item in a cache will be pushed down
      # to lower memory if capacity in the cache is reached. If lower
      # memory is backing store, then write a dirty item to store;
      # otherwise, if not dirty, no-op.
      #
      # Args:
      #     key: string representing the key
      #     val: data representing a value to store
      #     dirty: bool to set the dirty flag. Defaults to True
      try:
         self._cache.pop(key)
      except KeyError:
         while (len(self._cache) >= self._capacity):
            k, v = self._popitem(False)
            try:
               if self._lower_mem is not None:
                  self._lower_mem._setitem(k, v.val, v.dirty)
            except AttributeError:
               if v.dirty:
                  self._lower_mem[k] = v.val
      self._cache[key] = Cache._Val(dirty, val)
      self._modify_dirty_if_notified()

   def _send_bs_nondirties(self, *more):
      # send backing store all nondirty items from existing caches
      #
      # parses all caches in the chain below for items whose dirty
      # flags are False and sends a dictionary of this to the backing
      # store if exists. Includes pairs from |*more|.
      #
      # Args:
      #     *more: (key, value) pairs to add on top of the ones in the
      #        caches.
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
      # returns the lowest memory in the chain
      #
      # The lowest memory in the chain is either of Cache or
      # BackingStore type.
      #
      # Returns:
      #     Cache or BackingStore representing the lowest memory in the
      #     chain.
      mem = self
      try:
         while mem.lower_mem is not None:
            mem = mem.lower_mem
      except AttributeError:
         pass
      return mem

   def _is_lowest_mem_bstore(self):
      # returns True if lowest memory is of type BackingStore
      #
      # False otherwise
      return isinstance(self._get_lowest_mem(), BackingStore)

   def __init__(self, capacity=10, init_values=None, lower_mem=None):
      """Instantiate a Cache object.

      Args:
         capacity: int specifying the capacity of the cache
         init_values: list of pairs or a dictionary to initialize the
            cache with
         lower_mem: Cache or BackingStore to link to self

      Raises:
         ValueError: capacity is less than 1
         TypeError: lower_mem is not of type Cache or BackingStore or
            init_values is not of type list or dict
      """
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

      if isinstance(init_values, list):
         new_od = []
         for pair in init_values:
            entry = pair[0], Cache._Val(True, pair[1])
            new_od.append(entry)
      elif isinstance(init_values, dict):
         new_od = {}
         for k, v in init_values.items():
            new_od[k] = Cache._Val(True, v)
      elif init_values is None:
         new_od = {}
      else:
         raise TypeError('init_values needs to be a list or dict')

      self._cache = OrderedDict(new_od)

   @property
   def capacity(self):
      """get/set capacity

      When setting capacity lower than the amount of items stored in
      the cache, items are removed from the beginning of the cache,
      that is, the LRU items.

      Args:
         new_cap: int specifying new capacity

      Returns:
         current capacity
      """
      return self._capacity

   @capacity.setter
   def capacity(self, new_cap):
      self._capacity = new_cap
      trim = len(self._cache) - self._capacity
      if (trim > 0):
         for i in range(trim):
            self.popitem(last=False)

   @property
   def lower_mem(self):
      """return lower memory instance

      Lower memory instance is the Cache or BackingStore object
      linked to this cache.
      """
      return self._lower_mem

   def __getitem__(self, key):
      """cache[key]

      Get the item associated to key |key|. The item will be searched
      for starting at self and moving down to lower memory. If an item
      is found, it is returned and the item is placed at the top cache
      with other items moving down in LRU order.

      Args:
         key: string representing the key

      Returns:
         the item belonging to |key|

      Raises:
         CacheMiss: |key| doesn't match anything in caches or backing
            store
      """
      item, from_bstore = self._recurs_pop_unless_from_bs(key)
      dirty = False if from_bstore else True
      self._send_bs_nondirties((key, item))
      self._setitem(key, item, dirty)
      return item

   def __setitem__(self, key, val):
      """cache[key] = val

      set (key, val) into the cache while moving items down in LRU
      order.

      Args:
         key: string representing key
         val: data to set with key |key|
      """
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
      """del cache[key]

      Removes item with key |key| from self cache

      Args:
         key: string representing key to remove
      """
      del self._cache[key]

   def __len__(self):
      """len(cache)

      Returns:
         number of items in self cache
      """
      return len(self._cache)

   def items(self):
      """return list of (key, value) pairs in self cache

      Returns:
         list of (key, value) pairs
      """
      return [(k, v.val) for k, v in self._cache.items()]

   def __iter__(self):
      """return iterator over keys in self cache

      Returns:
         iterator over keys in self cache
      """
      return iter(self._cache)

   def keys(self):
      """return list of keys in self cache

      Returns:
         list of keys in self cache
      """
      return list(self._cache.keys())

   def values(self):
      """return list of values in self cache

      Returns:
         list of values in self cache
      """
      return [v.val for v in self._cache.values()]

   def __str__(self):
      """return string representation of self cache

      string representation is the following:
      "Cache: [(k0, v0), (k1, v1), ... (kn, vn)]"

      Returns:
         string representation of self cache
      """
      return "Cache: [" + \
             ", ".join(
                ["({}, {})".format(
                   k, v) for k, v in self._items()]) + \
             "]"

   def __contains__(self, key):
      """return True if key is in the self cache

      Args:
         key: string representing the key
      """
      return key in self._cache

   def get(self, key, default=None):
      """return the value of |key| if exists in self cache

      Default otherwise.

      Args:
         key: string representing the key
         default: value returned if key doesn't exist. Defaults to None

      Returns:
         value of |key| if exists in self cache; otherwise returns
         default
      """
      got = self._cache.get(key, default)
      return got.val if got is not default else got

   def __eq__(self, other):
      """return True if self is equal to |other| Cache

      Equal if self cache has the same (key, value) pairs in the same
      order and if capacity is the same. Values are different if the
      dirty flags differ.

      Args:
         other: another Cache instance

      Returns:
         True if self and |other| Cache instances are the same; False
         otherwise.
      """
      return self._cache == other._cache and \
             self._capacity == other._capacity

   def __ne__(self, other):
      """return True if self is not equal to |other| Cache

      See __eq__() for description of Cache equality

      Args:
         other: another Cache instance

      Returns:
         True if self and |other| Cache instances are different. False
         otherwise.
      """
      return not (self == other)

   def pop(self, key, default=__marker):
      """If exists, remove |key| from self cache and return its value

      Otherwise, return default. If default is not specified a KeyError
      is raised.

      Args:
         key: string representing the key
         default: default value to return if |key| doesn't exist.

      Return:
         Value of key if exists

      Raises:
         KeyError: key doesn't exist
      """
      return self._pop(key, default, True)

   def popitem(self, last=True):
      """Remove and return (key, value) pair in self cache

      Removes and returns the last (key, value) pair if last is True;
      otherwise, returns the first (key, value) pair. The first
      (key, value) pair is the LRU item, that is, removing the last
      item in the cache goes in LIFO order.

      Args:
         last: if True, returns last item in cache (LIFO). Defaults
            to True. False returns first item in cache (FIFO).

      Returns:
         last item in cache or first item in cache. This is a
         (key, value) pair.
      """
      return self._popitem(last, True)

   def clear(self):
      """Remove all items in the self cache"""
      self._cache.clear()

   def update(self, other):
      """update self cache with items from other cache

      (key, value) pairs from other overwrite existing keys

      Args:
         other: other Cache instance
      """
      self._cache.update(other._items())

   def setdefault(self, key, default=None):
      """return key's value if key is in self cache

      Otherwise insert key with a value of |default| and return default.

      Args:
         default: if key doesn't exist in cache, insert the key with
            this value and return it

      Returns:
         the value of |key| if exists in self cache, otherwise default
      """
      try:
         return self[key]
      except CacheMiss:
         self[key] = default
         return default

   def open_bstore(self):
      """open backing store

      if lowest memory in the chain is a BackingStore object

      Raises:
         NoBStoreError: lowest memory in the chain is not a BackingStore
            object
      """
      if not self._is_lowest_mem_bstore():
         raise NoBStoreError
      bs = self._get_lowest_mem()
      bs.open()

   def close_bstore(self):
      """close backing store

      if lowest memory in the chain is a BackingStore object.
      No-op otherwise.
      """
      if self._is_lowest_mem_bstore():
         bs = self._get_lowest_mem()
         bs.close()

   def bstore_closed(self):
      """return True if backing store is closed

      If lowest memroy in the chain is not a BackingStore object,
      True is returned anyway.

      Returns:
         True if backing store closed or nonexistent; False otherwise
      """
      if self._is_lowest_mem_bstore():
         bs = self._get_lowest_mem()
         return bs.closed()
      else:
         return True

   def __enter__(self):
      """opens the backing store using the "with" context manager

      calls open_bstore(). See above for description.

      Returns:
         self
      """
      self.open_bstore()
      return self

   def __exit__(self, exc_type, exc_val, exc_tb):
      """closes the backing store at the end of the "with" context

      calls close_bstore(). See above for description.

      Raises:
         any exceptions thrown in the "with" context
      """
      self.close_bstore()
      return False
