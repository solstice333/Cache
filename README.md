# Cache

## Description/Design:

This cache is implemented in Python 3.5 using PyCharm and aims to have the
functionality of an LRU, write-back, write allocate cache as described here:
https://en.wikipedia.org/wiki/Cache_(computing). The user has the option of
linking these caches to create a multilevel cache as well as choosing the
capacity for each cache. Alongside these caches, is a backing store. If data in
the lowest level cache runs out of space (due to a write to the top level
cache), and needs to demote and entry down, that entry, if dirty, is written to
the backing store automatically. When data is fetched from a multilevel cache,
that entry is searched top to bottom handling any cache misses, and if it
exists, it is promoted back to the top level cache. If it was fetched from the
backing store, it is marked as non-dirty, otherwise it is still dirty. If the
entry is not found in the backing store or the lowest level memory, it is
considered to be the "final" cache miss and a CacheMiss exception is raised.
The user can use simple try/except handling to handle this as desired. Any type
of data is permitted into the cache and backing store.

There are two main classes -- the Cache class and the BackingStore class. Both
implement the collections.abc.MutableMapping interfaces which take advantage
of Python (Abstract Base Classes) ABC's to define a dictionary-like interface. 
There are also three main exceptions included in the cache module -- the 
CacheMiss exception for whenever a cache miss occurs, the NoBStoreError 
exception for when an operation is done that requires a backing store to 
exist at the bottom of the memory chain, and the BStoreClosedError exception
for when an operation is done that requires the backing store to be open.

The Cache class is a wrapper on top of collections.OrderedDict that creates
a FIFO where any new entry is added to the tail, while the LRU entry is popped
from the head and pushed to the next level cache if that exists; otherwise it
is dropped or added to the backing store if that exists. Likewise, if 
an existing value in one of the caches is fetched, it would be popped from its
current location and pushed to the tail at the top level cache. If it is 
fetched from the backing store, it is almost all the time NOT popped from 
there, since its purpose is persistence, but still copied into the top level 
cache marked as non-dirty. The only special case where a fetched value from
the backing store is popped is if capacity is full in all memory levels and
a new dirty value needs to be written into the backing store. In other words,
the backing store tries to prioritize not popping out any values that are marked
non-dirty in the caches. If this is not possible, and something needs to be
popped out, the cache holding the matching entry of the popped entry previously
in the backing store, then, marks that entry as dirty to make sure 
it resynchronizes with the backing store later on.

The BackingStore class is a wrapper on top of shelve, a persistent 
dictionary-like object. As mentioned above, the backing store will receive
entries from the last cache in the chain if the entry is considered dirty.
When the entry is dirty, that just means it hasn't been written to the
persistence layer yet and thus requires synchronization. When the backing
store reaches maximum capacity and needs to kick out an entry that exists
in cache, it will notify the cache, who has that entry, to mark the entry as
dirty.

## Test Plan:

The test plan uses the unittest module and involves the following unit tests:
1. setUp(): method test fundamental Cache ctors
2. test_cache_ctor_lower_mem_type_enforce(): test type enforcement of the `lower_mem` keyword arg which must be Cache or BackingStore only
3. test_contains(): test `__contains__()` method for Cache 
4. test_eq_ne(): test `__eq__()`, `__ne__()` methods for Cache and Cache._Val
5. test_getitem(): test `__getitem__()` method for Cache
6. test_setitem(): test `__setitem__()` method for Cache
7. test_del(): test `__delitem__()` method for Cache
8. test_iter(): test `__iter__()` method for Cache
9. test_len(): test `__len__()` method for Cache
10. test_str(): test `__str__()` method for Cache
11. test_clear(): test `clear()` method for Cache
12. test_get(): test `get()` method for Cache
13. test_items(): test `items()` method for Cache
14. test_keys(): test `keys()` method for Cache
15. test_values(): test `values()` method for Cache
16. test_pop(): test `pop()` method for Cache
17. test_popitem(): test `popitem()` method for Cache
18. test_update(): test `update()` method for Cache
19. test_set_default(): test `setdefault()` method for Cache
20. test_cap_change(): test changing capacity property for Cache
21. test_lru_func(): test LRU replacement policy
22. test_cache_double_lv(): test a double level cache
23. test_cache_triple_lv(): test a triple level cache
24. test_bstore(): test all methods in BackingStore class
25. test_capacity(): assert that setting capacity < 1 raises a ValueError
26. test_2_lv_cache_with_bstore(): integration test testing 2 level cache with a backing store
27. test_recommended_usage_example(): test the recommended usage of Cache/BackingStore which utilizes the with context manager

## Usage:

Here's how to run the unit tests:

```
   $ cd path/to/Cache
   $ env PYTHONPATH=.:$PYTHONPATH python tests/cache_test.py
```

The following is a simple example of the recommended way to use the cache API 
as shown in the test_recommended_usage_example() unit test. It creates
a backing store with a capacity of 3 entries, a level 2 cache with a 
capacity of 2 entries, and a level 1 cache with a capacity of 1 entry.

```
   bs = BackingStore(3)
   c2 = Cache(2, lower_mem=bs)
   with Cache(1, lower_mem=c2) as top_cache: # opens the backing store
      top_cache['a'] = 1
      top_cache['b'] = 2
      top_cache['c'] = 3
      top_cache['d'] = 4
      top_cache['e'] = 5
      top_cache['f'] = 6
      foo = top_cache['d'] # grabs 4, puts 'd' at the tail of the lv1 cache
      bar = top_cache['b'] # grabs 2, puts 'b' at the tail of the lv1 cache
                           # and pushes 'd' to the tail of the lv2 cache
```

## API:

The entire API help doc can be outputted to console with the following 
commands:

```
$ cd path/to/Cache # replace path/to/Cache with the actual path
$ python -c "import cache; help(cache)" 
```

Which would output:

```
NAME
    cache

CLASSES
    builtins.Exception(builtins.BaseException)
        BStoreClosedError
        CacheMiss
        NoBStoreError
    collections.abc.MutableMapping(collections.abc.Mapping)
        BackingStore
        Cache
    
    class BStoreClosedError(builtins.Exception)
     |  exception for when a backing store hasn't been opened yet
     |  
     |  Method resolution order:
     |      BStoreClosedError
     |      builtins.Exception
     |      builtins.BaseException
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __str__(self)
     |      return string representation of BStoreClosedError
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from builtins.Exception:
     |  
     |  __init__(self, /, *args, **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  __new__(*args, **kwargs) from builtins.type
     |      Create and return a new object.  See help(type) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from builtins.BaseException:
     |  
     |  __delattr__(self, name, /)
     |      Implement delattr(self, name).
     |  
     |  __getattribute__(self, name, /)
     |      Return getattr(self, name).
     |  
     |  __reduce__(...)
     |      helper for pickle
     |  
     |  __repr__(self, /)
     |      Return repr(self).
     |  
     |  __setattr__(self, name, value, /)
     |      Implement setattr(self, name, value).
     |  
     |  __setstate__(...)
     |  
     |  with_traceback(...)
     |      Exception.with_traceback(tb) --
     |      set self.__traceback__ to tb and return self.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from builtins.BaseException:
     |  
     |  __cause__
     |      exception cause
     |  
     |  __context__
     |      exception context
     |  
     |  __dict__
     |  
     |  __suppress_context__
     |  
     |  __traceback__
     |  
     |  args
    
    class BackingStore(collections.abc.MutableMapping)
     |  Backing Store class. Link this to a Cache object
     |  
     |  This class represents a backing store which is the lowest storage to
     |  write to after all levels of caches has missed. It is considered
     |  persistent non-volatile storage. This class implements the
     |  collections.abc.MutableMapping interface which acts as a wrapper on top
     |  of shelve.
     |  
     |  Method resolution order:
     |      BackingStore
     |      collections.abc.MutableMapping
     |      collections.abc.Mapping
     |      collections.abc.Sized
     |      collections.abc.Iterable
     |      collections.abc.Container
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __contains__(self, key)
     |      |key| in obj
     |      
     |      return True if backing store has key; False otherwise
     |      
     |      Args:
     |         key: string representing the key
     |      
     |      Returns:
     |         True if |key| is in backing store; False otherwise
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  __delitem__(self, key)
     |      del obj[key]
     |      
     |      delete data from backing store
     |      
     |      Args:
     |         key: string representing key
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  __enter__(self)
     |      Open the backing store and return self using the with statement
     |      
     |      Returns:
     |         self
     |  
     |  __eq__(self, other)
     |      return True if equal; False otherwise
     |      
     |      Equal if |other| store contents have the same (key, value) pairs
     |      and capacity is the same as self.
     |      
     |      Args:
     |         other: another BackingStore instance
     |      
     |      Returns:
     |         True if equal; False otherwise
     |  
     |  __exit__(self, exc_type, exc_val, exc_tb)
     |      Closes the backing store
     |      
     |      Raises:
     |         any exception raised from within the runtime context
     |  
     |  __getitem__(self, key)
     |      obj[key]
     |      
     |      get data from backing store
     |      
     |      Args:
     |         key: string representing the key to look for
     |      
     |      Returns:
     |         The data associated with |key|
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |         KeyError: |key| doesn't exist
     |  
     |  __init__(self, capacity=10, dbname='bstore')
     |      BackingStore ctor
     |      
     |      Instantiate a BackingStore object with a maximum capacity of
     |      |capacity|, and writes data to a file named "|dbname|.db".
     |      
     |      Args:
     |         capacity: integer specifying the maximum capacity the database
     |            can hold. Default is 10.
     |         dbname: string representing the name of the database/store.
     |            Default is 'bstore'
     |  
     |  __iter__(self)
     |      return an iterator over the keys in the backing store
     |      
     |      Returns:
     |         iterator over the keys in the backing store
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  __len__(self)
     |      return the number of itmes in the backing store
     |      
     |      Returns:
     |         number of items in the backing store
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  __ne__(self, other)
     |      return True if not equal; False otherwise
     |      
     |      Not equal if |other| store contents have different (key, value)
     |      pairs or capacity is different from self
     |      
     |      Args:
     |         other: another BackingStore instance
     |      
     |      Returns:
     |         True if not equal; False otherwise
     |  
     |  __setitem__(self, key, value)
     |      obj[key] = value
     |      
     |      set data in backing store
     |      
     |      Args:
     |         key: string representing the key to associate |value| with
     |         value: any data bound to |key|
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  __str__(self)
     |      return a string representation of the backing store
     |      
     |      A string representation of the backing store is all the
     |      (key, value) pairs sorted by key and listed out. If
     |      backing store is closed, prints out "BackingStore: closed".
     |      
     |      Returns:
     |         string representation of the backing store
     |  
     |  clear(self)
     |      remove all (key, value) pairs from the store
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  close(self)
     |      close the backing store i/o stream
     |  
     |  closed(self)
     |      return True if backing store is closed; False otherwise
     |  
     |  get(self, key, default=None)
     |      return the value for |key| if |key| is in the store
     |      
     |      Args:
     |         key: string representing the key
     |      
     |      Returns:
     |         value for |key|
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  items(self)
     |      return a list of (key, value) pairs contained in the backing store
     |      
     |      Returns:
     |         a list of (key, value) pairs contained in the backing store
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  keys(self)
     |      return a list of the keys in the backing store
     |      
     |      Returns:
     |         a list of all the keys in the backing store
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  open(self)
     |      open the backing store i/o stream
     |      
     |      On opening, if the shelve content length is too large, it is
     |      reduced down to the maximum capacity. Data is removed randomly.
     |  
     |  pop(self, key, default=<object object at 0x10282e0a0>)
     |      Remove |key| and return its value if exists in store
     |      
     |      If |key| is in the store, return the value of |key|; otherwise
     |      return |default|.
     |      
     |      Args:
     |         key: string representing the key
     |         default: any data type representing the default return value
     |            if |key| is not in store. If |default| is not given, a
     |            KeyError is raised.
     |      
     |      Returns:
     |         the value associated to |key|, else |default|.
     |      
     |      Raises:
     |         KeyError: |key| is not in store
     |         BStoreClosedError: backing store is closed
     |  
     |  popitem(self)
     |      Remove and return a (key, value) pair from store
     |      
     |      First, check to see if a key that exists in the store is a key
     |      who's dirty value in the upper caches is False. If it is, then
     |      remove that (key, value) pair and return it. Otherwise, remove
     |      an arbitrary (key, value) pair and return it. The caches above
     |      are notified of the removed (key, value) pair so that they
     |      can automatically synchronize the dirty value if needed. That is,
     |      if a (key, value) pair is removed whose key is in the cache and
     |      its value isn't dirty, it will be modified to be dirty so it
     |      can be written back to the store.
     |      
     |      Returns:
     |         the (key, value) pair removed from the store
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  setdefault(self, key, default=None)
     |      return key's value if in store, otherwise insert key
     |      
     |      If |key| is in store, return its value, otherwise insert key
     |      with a value of |default|.
     |      
     |      Args:
     |         key: string representing the key
     |         default: the value to insert if |key| doesn't exist in store.
     |            Defaults to None.
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  update(self, other)
     |      updates the store with (key, value) pairs from another store
     |      
     |      Update the store with (key, value) pairs from the |other| store;
     |      Existing keys are overwritten.
     |      
     |      Args:
     |         other: another BackingStore instance
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  values(self)
     |      return a list of the values in the backing store
     |      
     |      Returns:
     |         a list of values contained in the backing store
     |      
     |      Raises:
     |         BStoreClosedError: backing store is closed
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  capacity
     |      get/set capacity of store
     |      
     |      On setting, if the backing store is open and the length of the store
     |      contents is greater than the capacity, the backing store contents is
     |      trimmed down to the new capacity. Data is removed randomly.
     |      
     |      Args:
     |         new_cap: int specifying new capacity
     |      
     |      Returns:
     |         current capacity
     |  
     |  dbname
     |      get name of database/store
     |      
     |      Returns:
     |         name of store
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  __abstractmethods__ = frozenset()
     |  
     |  __hash__ = None
     |  
     |  ----------------------------------------------------------------------
     |  Class methods inherited from collections.abc.Sized:
     |  
     |  __subclasshook__(C) from abc.ABCMeta
     |      Abstract classes can override this to customize issubclass().
     |      
     |      This is invoked early on by abc.ABCMeta.__subclasscheck__().
     |      It should return True, False or NotImplemented.  If it returns
     |      NotImplemented, the normal algorithm is used.  Otherwise, it
     |      overrides the normal algorithm (and the outcome is cached).
    
    class Cache(collections.abc.MutableMapping)
     |  Cache class. Cache and BackingStore objects can be linked to this
     |  
     |  Represents a cache that adheres to an LRU replacement policy,
     |  write-back, and write allocate policy. If a backing store is linked
     |  downstream, the dirty values in the (key, value) pairs contained
     |  in the upper caches are updated accordingly. That is, if a
     |  (key, value) pair is removed from the backing store whose
     |  key in the upper cache is marked as non-dirty, it is then marked
     |  as dirty.
     |  
     |  Method resolution order:
     |      Cache
     |      collections.abc.MutableMapping
     |      collections.abc.Mapping
     |      collections.abc.Sized
     |      collections.abc.Iterable
     |      collections.abc.Container
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __contains__(self, key)
     |      return True if key is in the self cache
     |      
     |      Args:
     |         key: string representing the key
     |  
     |  __delitem__(self, key)
     |      del cache[key]
     |      
     |      Removes item with key |key| from self cache
     |      
     |      Args:
     |         key: string representing key to remove
     |  
     |  __enter__(self)
     |      opens the backing store using the "with" context manager
     |      
     |      calls open_bstore(). See above for description.
     |      
     |      Returns:
     |         self
     |  
     |  __eq__(self, other)
     |      return True if self is equal to |other| Cache
     |      
     |      Equal if self cache has the same (key, value) pairs in the same
     |      order and if capacity is the same. Values are different if the
     |      dirty flags differ.
     |      
     |      Args:
     |         other: another Cache instance
     |      
     |      Returns:
     |         True if self and |other| Cache instances are the same; False
     |         otherwise.
     |  
     |  __exit__(self, exc_type, exc_val, exc_tb)
     |      closes the backing store at the end of the "with" context
     |      
     |      calls close_bstore(). See above for description.
     |      
     |      Raises:
     |         any exceptions thrown in the "with" context
     |  
     |  __getitem__(self, key)
     |      cache[key]
     |      
     |      Get the item associated to key |key|. The item will be searched
     |      for starting at self and moving down to lower memory. If an item
     |      is found, it is returned and the item is placed at the top cache
     |      with other items moving down in LRU order.
     |      
     |      Args:
     |         key: string representing the key
     |      
     |      Returns:
     |         the item belonging to |key|
     |      
     |      Raises:
     |         CacheMiss: |key| doesn't match anything in caches or backing
     |            store
     |  
     |  __init__(self, capacity=10, init_values=None, lower_mem=None)
     |      Instantiate a Cache object.
     |      
     |      Args:
     |         capacity: int specifying the capacity of the cache
     |         init_values: list of pairs or a dictionary to initialize the
     |            cache with
     |         lower_mem: Cache or BackingStore to link to self
     |      
     |      Raises:
     |         ValueError: capacity is less than 1
     |         TypeError: lower_mem is not of type Cache or BackingStore or
     |            init_values is not of type list or dict
     |  
     |  __iter__(self)
     |      return iterator over keys in self cache
     |      
     |      Returns:
     |         iterator over keys in self cache
     |  
     |  __len__(self)
     |      len(cache)
     |      
     |      Returns:
     |         number of items in self cache
     |  
     |  __ne__(self, other)
     |      return True if self is not equal to |other| Cache
     |      
     |      See __eq__() for description of Cache equality
     |      
     |      Args:
     |         other: another Cache instance
     |      
     |      Returns:
     |         True if self and |other| Cache instances are different. False
     |         otherwise.
     |  
     |  __setitem__(self, key, val)
     |      cache[key] = val
     |      
     |      set (key, val) into the cache while moving items down in LRU
     |      order.
     |      
     |      Args:
     |         key: string representing key
     |         val: data to set with key |key|
     |  
     |  __str__(self)
     |      return string representation of self cache
     |      
     |      string representation is the following:
     |      "Cache: [(k0, v0), (k1, v1), ... (kn, vn)]"
     |      
     |      Returns:
     |         string representation of self cache
     |  
     |  bstore_closed(self)
     |      return True if backing store is closed
     |      
     |      If lowest memroy in the chain is not a BackingStore object,
     |      True is returned anyway.
     |      
     |      Returns:
     |         True if backing store closed or nonexistent; False otherwise
     |  
     |  clear(self)
     |      Remove all items in the self cache
     |  
     |  close_bstore(self)
     |      close backing store
     |      
     |      if lowest memory in the chain is a BackingStore object.
     |      No-op otherwise.
     |  
     |  get(self, key, default=None)
     |      return the value of |key| if exists in self cache
     |      
     |      Default otherwise.
     |      
     |      Args:
     |         key: string representing the key
     |         default: value returned if key doesn't exist. Defaults to None
     |      
     |      Returns:
     |         value of |key| if exists in self cache; otherwise returns
     |         default
     |  
     |  items(self)
     |      return list of (key, value) pairs in self cache
     |      
     |      Returns:
     |         list of (key, value) pairs
     |  
     |  keys(self)
     |      return list of keys in self cache
     |      
     |      Returns:
     |         list of keys in self cache
     |  
     |  open_bstore(self)
     |      open backing store
     |      
     |      if lowest memory in the chain is a BackingStore object
     |      
     |      Raises:
     |         NoBStoreError: lowest memory in the chain is not a BackingStore
     |            object
     |  
     |  pop(self, key, default=<object object at 0x10282e0b0>)
     |      If exists, remove |key| from self cache and return its value
     |      
     |      Otherwise, return default. If default is not specified a KeyError
     |      is raised.
     |      
     |      Args:
     |         key: string representing the key
     |         default: default value to return if |key| doesn't exist.
     |      
     |      Return:
     |         Value of key if exists
     |      
     |      Raises:
     |         KeyError: key doesn't exist
     |  
     |  popitem(self, last=True)
     |      Remove and return (key, value) pair in self cache
     |      
     |      Removes and returns the last (key, value) pair if last is True;
     |      otherwise, returns the first (key, value) pair. The first
     |      (key, value) pair is the LRU item, that is, removing the last
     |      item in the cache goes in LIFO order.
     |      
     |      Args:
     |         last: if True, returns last item in cache (LIFO). Defaults
     |            to True. False returns first item in cache (FIFO).
     |      
     |      Returns:
     |         last item in cache or first item in cache. This is a
     |         (key, value) pair.
     |  
     |  setdefault(self, key, default=None)
     |      return key's value if key is in self cache
     |      
     |      Otherwise insert key with a value of |default| and return default.
     |      
     |      Args:
     |         default: if key doesn't exist in cache, insert the key with
     |            this value and return it
     |      
     |      Returns:
     |         the value of |key| if exists in self cache, otherwise default
     |  
     |  update(self, other)
     |      update self cache with items from other cache
     |      
     |      (key, value) pairs from other overwrite existing keys
     |      
     |      Args:
     |         other: other Cache instance
     |  
     |  values(self)
     |      return list of values in self cache
     |      
     |      Returns:
     |         list of values in self cache
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  capacity
     |      get/set capacity
     |      
     |      When setting capacity lower than the amount of items stored in
     |      the cache, items are removed from the beginning of the cache,
     |      that is, the LRU items.
     |      
     |      Args:
     |         new_cap: int specifying new capacity
     |      
     |      Returns:
     |         current capacity
     |  
     |  lower_mem
     |      return lower memory instance
     |      
     |      Lower memory instance is the Cache or BackingStore object
     |      linked to this cache.
     |  
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  
     |  __abstractmethods__ = frozenset()
     |  
     |  __hash__ = None
     |  
     |  ----------------------------------------------------------------------
     |  Class methods inherited from collections.abc.Sized:
     |  
     |  __subclasshook__(C) from abc.ABCMeta
     |      Abstract classes can override this to customize issubclass().
     |      
     |      This is invoked early on by abc.ABCMeta.__subclasscheck__().
     |      It should return True, False or NotImplemented.  If it returns
     |      NotImplemented, the normal algorithm is used.  Otherwise, it
     |      overrides the normal algorithm (and the outcome is cached).
    
    class CacheMiss(builtins.Exception)
     |  exception for a cache miss
     |  
     |  Method resolution order:
     |      CacheMiss
     |      builtins.Exception
     |      builtins.BaseException
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __str__(self)
     |      return string representation of CacheMiss
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from builtins.Exception:
     |  
     |  __init__(self, /, *args, **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  __new__(*args, **kwargs) from builtins.type
     |      Create and return a new object.  See help(type) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from builtins.BaseException:
     |  
     |  __delattr__(self, name, /)
     |      Implement delattr(self, name).
     |  
     |  __getattribute__(self, name, /)
     |      Return getattr(self, name).
     |  
     |  __reduce__(...)
     |      helper for pickle
     |  
     |  __repr__(self, /)
     |      Return repr(self).
     |  
     |  __setattr__(self, name, value, /)
     |      Implement setattr(self, name, value).
     |  
     |  __setstate__(...)
     |  
     |  with_traceback(...)
     |      Exception.with_traceback(tb) --
     |      set self.__traceback__ to tb and return self.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from builtins.BaseException:
     |  
     |  __cause__
     |      exception cause
     |  
     |  __context__
     |      exception context
     |  
     |  __dict__
     |  
     |  __suppress_context__
     |  
     |  __traceback__
     |  
     |  args
    
    class NoBStoreError(builtins.Exception)
     |  exception for no backing store linked to the cache
     |  
     |  Method resolution order:
     |      NoBStoreError
     |      builtins.Exception
     |      builtins.BaseException
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __str__(self)
     |      return string representation of NoBStoreError
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from builtins.Exception:
     |  
     |  __init__(self, /, *args, **kwargs)
     |      Initialize self.  See help(type(self)) for accurate signature.
     |  
     |  __new__(*args, **kwargs) from builtins.type
     |      Create and return a new object.  See help(type) for accurate signature.
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from builtins.BaseException:
     |  
     |  __delattr__(self, name, /)
     |      Implement delattr(self, name).
     |  
     |  __getattribute__(self, name, /)
     |      Return getattr(self, name).
     |  
     |  __reduce__(...)
     |      helper for pickle
     |  
     |  __repr__(self, /)
     |      Return repr(self).
     |  
     |  __setattr__(self, name, value, /)
     |      Implement setattr(self, name, value).
     |  
     |  __setstate__(...)
     |  
     |  with_traceback(...)
     |      Exception.with_traceback(tb) --
     |      set self.__traceback__ to tb and return self.
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors inherited from builtins.BaseException:
     |  
     |  __cause__
     |      exception cause
     |  
     |  __context__
     |      exception context
     |  
     |  __dict__
     |  
     |  __suppress_context__
     |  
     |  __traceback__
     |  
     |  args
```


