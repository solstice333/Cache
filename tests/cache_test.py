#!/usr/bin/env python3.5
import unittest
from cache import *
from copy import deepcopy
import os.path
import os
import string


class CacheTest(unittest.TestCase):
   @staticmethod
   def cascade_dump(cache):
      mem = cache
      s = "cascade dump:\n"

      while mem is not None:
         s += "   {}\n".format(mem)
         try:
            mem = mem.lower_mem
         except AttributeError:
            break
      return s

   @staticmethod
   def rm_or_noop(file):
      if os.path.isfile(file):
         os.remove(file)

   def setUp(self):
      d = {'cherry':3, 'blueberry':1, 'strawberry':2}
      self.c1 = Cache()
      self.c2 = Cache(init_values=sorted(d.items()))
      self.c3 = Cache(init_values=[('foo',1),('bar',2)])
      self.c4 = Cache(init_values={'a':1, 'b':2})

      self.assertRaises(TypeError, Cache, init_values='foo')

   def test_cache_ctor_lower_mem_type_enforce(self):
      with self.assertRaises(TypeError) as te:
         Cache(lower_mem=1)
      self.assertEqual(
         str(te.exception),
         "lower_mem must be None or of type Cache or BackingStore")

   def test_contains(self):
      self.assertTrue('strawberry' in self.c2)
      self.assertFalse('strawberry' in self.c1)

   def test_eq_ne(self):
      self.assertEqual(self.c2, Cache(
         init_values=[('blueberry',1), ('cherry',3), ('strawberry',2)]))
      self.assertNotEqual(self.c2, Cache(capacity=20,
         init_values=[('blueberry', 1), ('cherry', 3), ('strawberry', 2)]))
      self.assertEqual(self.c1, Cache())
      self.assertNotEqual(self.c1, Cache(capacity=20))

      v1 = Cache._Val(True, 3)
      v2 = Cache._Val(True, 3)
      v3 = Cache._Val(False, 3)
      v4 = Cache._Val(True, 4)
      self.assertEqual(v1, v2)
      self.assertNotEqual(v1, v3)
      self.assertNotEqual(v1, v4)

   def test_getitem(self):
      c2 = self.c2
      self.assertEqual(c2['cherry'], 3)
      self.assertEqual(c2, Cache(
         init_values=[('blueberry',1), ('strawberry',2), ('cherry',3)]))
      self.assertEqual(c2['blueberry'], 1)
      self.assertEqual(c2, Cache(
         init_values=[('strawberry',2), ('cherry',3), ('blueberry',1)]))
      self.assertEqual(c2['strawberry'], 2)
      self.assertEqual(c2, Cache(
         init_values=[('cherry', 3), ('blueberry', 1), ('strawberry', 2)]))
      self.assertEqual(len(c2), 3)

   def test_setitem(self):
      c = Cache()
      c['foo'] = 1
      self.assertEqual(c, Cache(init_values=[('foo',1)]))
      c['bar'] = 2
      self.assertEqual(c, Cache(init_values=[('foo',1), ('bar',2)]))
      c['foo'] = 3
      self.assertEqual(c, Cache(init_values=[('bar',2), ('foo',3)]))

   def test_del(self):
      c2 = self.c2
      self.assertTrue('cherry' in c2)
      del c2['cherry']
      self.assertFalse('cherry' in c2)

   def test_iter(self):
      c2 = self.c2
      i1 = iter(c2.items())
      i2 = iter(c2.items())

      self.assertEqual(next(i1), ('blueberry', 1))
      self.assertEqual(next(i1), ('cherry', 3))
      self.assertEqual(next(i2), ('blueberry', 1))
      self.assertEqual(next(i2), ('cherry', 3))
      self.assertEqual(next(i2), ('strawberry', 2))
      self.assertRaises(StopIteration, next, i2)

   def test_len(self):
      self.assertEqual(len(self.c2), 3)
      self.assertEqual(len(self.c1), 0)
      self.assertEqual(len(self.c3), 2)
      self.assertEqual(len(self.c4), 2)

   def test_str(self):
      self.assertEqual(str(self.c2),
                       'Cache: ['
                       '(blueberry, (True, 1)), '
                       '(cherry, (True, 3)), '
                       '(strawberry, (True, 2))]')

   def test_clear(self):
      c = deepcopy(self.c3)
      self.assertEqual(len(c), 2)
      c.clear()
      self.assertEqual(len(c), 0)

   def test_get(self):
      self.assertEqual(self.c2.get('strawberry'), 2)
      self.assertEqual(self.c1.get('strawberry'), None)
      self.assertEqual(self.c1.get('strawberry', 0), 0)

   def test_items(self):
      c = deepcopy(self.c3)
      self.assertEqual(list(c.items()), [('foo',1), ('bar',2)])

   def test_keys(self):
      c = deepcopy(self.c3)
      self.assertEqual(list(c.keys()), ['foo', 'bar'])

   def test_values(self):
      c = deepcopy(self.c3)
      self.assertEqual(list(c.values()), [1, 2])

   def test_pop(self):
      c = deepcopy(self.c3)
      self.assertEqual(c.pop('foo'), 1)
      self.assertEqual(c.pop('foo', None), None)
      self.assertEqual(c.pop('foo', 0), 0)
      self.assertRaises(KeyError, c.pop, 'foo')

   def test_popitem(self):
      c = deepcopy(self.c2)
      self.assertEqual(c.popitem(), ('strawberry', 2))
      self.assertEqual(c, Cache(init_values=[('blueberry',1), ('cherry',3)]))
      self.assertEqual(c.popitem(False), ('blueberry', 1))
      self.assertEqual(c, Cache(init_values=[('cherry',3)]))

   def test_update(self):
      c1 = deepcopy(self.c1)
      c2 = deepcopy(self.c2)
      c3 = deepcopy(self.c3)
      c1.update(c3)
      c1.update(c2)
      self.assertEqual(c1, Cache(
         init_values=[('foo', 1), ('bar', 2), ('blueberry', 1),
          ('cherry', 3), ('strawberry', 2)]))

   def test_set_default(self):
      c2 = deepcopy(self.c2)
      self.assertEqual(c2.setdefault('blueberry'), 1)
      self.assertEqual(c2.setdefault('mango'), None)
      self.assertEqual(c2['mango'], None)
      self.assertEqual(c2.setdefault('blueberry', 100), 1)
      self.assertEqual(c2.setdefault('peach', 200), 200)
      self.assertEqual(c2['peach'], 200)

   def test_cap_change(self):
      c = deepcopy(self.c3)
      c.update(self.c2)
      c.capacity = 6
      self.assertEqual(
         c, Cache(capacity=6,
                  init_values=[('foo', 1), ('bar', 2), ('blueberry', 1),
                               ('cherry', 3), ('strawberry', 2)]))

      c.capacity = 5
      self.assertEqual(
         c, Cache(capacity=5,
                  init_values=[('foo', 1), ('bar', 2), ('blueberry', 1),
                               ('cherry', 3), ('strawberry', 2)]))
      c.capacity = 4
      self.assertEqual(
         c, Cache(capacity=4,
                  init_values=[('foo', 1), ('bar', 2), ('blueberry', 1),
                               ('cherry', 3)]))

   def test_lru_func(self):
      c = deepcopy(self.c2)
      c.capacity = 4
      c['tangerine'] = 4
      c['mango'] = 5
      c['strawberry'] = 6
      self.assertEqual(
         c, Cache(capacity=4,
                  init_values=[('cherry', 3), ('tangerine', 4),
                               ('mango', 5), ('strawberry', 6)]))

   def test_cache_double_lv(self):
      def create_caches():
         c2 = Cache(4, [('c', 3), ('d', 4)])
         c1 = Cache(2, [('a', 1)], lower_mem=c2)
         return c1

      c1 = create_caches()
      cexp2 = Cache(4, [('c', 3), ('d', 4)])
      cexp1 = Cache(2, [('a', 1)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "expect double lv cache instantiation")

      c1['d']
      cexp2 = Cache(4, [('c', 3)])
      cexp1 = Cache(2, [('a', 1), ('d', 4)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "get d from 2nd lv, empty slot in 1st lv")

      c1 = create_caches()
      c1['c']
      cexp2 = Cache(4, [('d', 4)])
      cexp1 = Cache(2, [('a', 1), ('c', 3)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "get c from 2nd level, empty slot in 1st lv")

      c1 = create_caches()
      c1['b'] = 2
      cexp2 = Cache(4, [('c', 3), ('d', 4)])
      cexp1 = Cache(2, [('a', 1), ('b', 2)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "set b, empty slot in 1st lv")

      c1['e'] = 5
      cexp2 = Cache(4, [('c', 3), ('d', 4), ('a', 1)])
      cexp1 = Cache(2, [('b', 2), ('e', 5)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "set e, demote a")

      c1['f'] = 6
      cexp2 = Cache(4, [('c', 3), ('d', 4), ('a', 1), ('b', 2)])
      cexp1 = Cache(2, [('e', 5), ('f', 6)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "set f, demote b")

      c1['c']
      cexp2 = Cache(4, [('d', 4), ('a', 1), ('b', 2), ('e', 5)])
      cexp1 = Cache(2, [('f', 6), ('c', 3)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "get c from 2nd lv head, demote e")

      c1['c']
      cexp2 = Cache(4, [('d', 4), ('a', 1), ('b', 2), ('e', 5)])
      cexp1 = Cache(2, [('f', 6), ('c', 3)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "get c, no-op")

      c1['f']
      cexp2 = Cache(4, [('d', 4), ('a', 1), ('b', 2), ('e', 5)])
      cexp1 = Cache(2, [('c', 3), ('f', 6)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "get f from 1st, put f at end of 1st")

      with self.assertRaises(CacheMiss, msg="cache miss getting g"):
         c1['g']

      c1['e']
      cexp2 = Cache(4, [('d', 4), ('a', 1), ('b', 2), ('c', 3)])
      cexp1 = Cache(2, [('f', 6), ('e', 5)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "get c from 2nd lv tail, demote e")

      c1['g'] = 7
      cexp2 = Cache(4, [('a', 1), ('b', 2), ('c', 3), ('f', 6)])
      cexp1 = Cache(2, [('e', 5), ('g', 7)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "set g, boot d")

   def test_cache_triple_lv(self):
      def create_caches():
         c3 = Cache(3, [])
         c2 = Cache(2, [('b', 2)], lower_mem=c3)
         c1 = Cache(1, [('a', 1)], lower_mem=c2)
         return c1

      c1 = create_caches()
      cexp3 = Cache(3, [])
      cexp2 = Cache(2, [('b', 2)], lower_mem=cexp3)
      cexp1 = Cache(1, [('a', 1)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "expect triple lv cache instantiation")

      c1['c'] = 3
      cexp3 = Cache(3, [])
      cexp2 = Cache(2, [('b', 2), ('a', 1)], lower_mem=cexp3)
      cexp1 = Cache(1, [('c', 3)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "set c, demote a to lv2")

      c1['d'] = 4
      cexp3 = Cache(3, [('b', 2)])
      cexp2 = Cache(2, [('a', 1), ('c', 3)], lower_mem=cexp3)
      cexp1 = Cache(1, [('d', 4)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1, "set d, demote c to lv2, demote b to lv3")

      c1['b']
      cexp3 = Cache(3, [('a', 1)])
      cexp2 = Cache(2, [('c', 3), ('d', 4)], lower_mem=cexp3)
      cexp1 = Cache(1, [('b', 2)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1,
                       "get b from 3rd, demote d to lv2, demote a to lv3")

      c1['e'] = 5
      c1['f'] = 6
      cexp3 = Cache(3, [('a', 1), ('c', 3), ('d', 4)])
      cexp2 = Cache(2, [('b', 2), ('e', 5)], lower_mem=cexp3)
      cexp1 = Cache(1, [('f', 6)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1,
                       "set e, f demote b, e to 2, demote c, d to 3")

      c1['g'] = 7
      cexp3 = Cache(3, [('c', 3), ('d', 4), ('b', 2)])
      cexp2 = Cache(2, [('e', 5), ('f', 6)], lower_mem=cexp3)
      cexp1 = Cache(1, [('g', 7)], lower_mem=cexp2)
      self.assertEqual(c1, cexp1,
                       "set g, demote f to 2, demote b to 3, boot out a")

   def test_bstore(self):
      def populate_bs(bs, len):
         max = 5
         for c, i in zip(string.ascii_lowercase[:len], range(1, max + 1)):
            bs[c] = i

      CacheTest.rm_or_noop('foo.db')
      CacheTest.rm_or_noop('bar.db')
      CacheTest.rm_or_noop('baz.db')

      bs = BackingStore()
      self.assertEqual(bs.capacity, 10)
      self.assertEqual(bs.dbname, 'bstore')

      bs = BackingStore(5, 'foo')
      self.assertTrue(bs.closed())
      bs.open()
      self.assertFalse(bs.closed())
      bs.close()
      self.assertTrue(bs.closed())
      self.assertTrue(os.path.isfile('foo.db'))

      bs.open()
      with self.assertRaises(KeyError):
         bs['a']
      bs['a'] = 1
      self.assertEqual(bs['a'], 1)
      self.assertEqual(len(bs), 1)
      bs['b'] = 2
      bs['c'] = 3
      bs['d'] = 4
      bs['e'] = 5
      bs['f'] = 6
      self.assertEqual(len(bs), 5)
      self.assertTrue(type(iter(bs)).__name__, 'generator')

      bs.clear()
      self.assertEqual(len(bs), 0)
      populate_bs(bs, 5)

      self.assertEqual(str(bs),
                       "BackingStore: [('a', 1), ('b', 2), ('c', 3), "
                       "('d', 4), ('e', 5)]")

      bs2 = BackingStore(4, 'bar')
      bs2.open()
      populate_bs(bs2, 4)
      self.assertNotEqual(bs, bs2)

      bs3 = BackingStore(5, 'baz')
      bs3.open()
      populate_bs(bs3, 5)
      self.assertEqual(bs, bs3)

      del bs['a']
      with self.assertRaises(KeyError):
         bs['a']

      self.assertTrue('b' in bs)
      self.assertFalse('a' in bs)

      self.assertEqual(sorted(bs.keys()), ['b', 'c', 'd', 'e'])
      self.assertEqual(sorted(bs.values()), [2, 3, 4, 5])
      self.assertEqual(sorted(bs.items()),
                       [('b', 2), ('c', 3), ('d', 4), ('e', 5)])

      self.assertEqual(bs.get('b'), 2)
      self.assertEqual(bs.get('a'), None)
      self.assertEqual(bs.get('b', 200), 2)
      self.assertEqual(bs.get('a', 200), 200)

      self.assertEqual(bs.pop('b'), 2)
      self.assertRaises(KeyError, bs.pop, 'b')
      self.assertEqual(bs.pop('b', 300), 300)
      self.assertEqual(bs.pop('c', 300), 3)

      bs.clear()
      populate_bs(bs, 5)

      self.assertTrue(isinstance(bs.popitem(), tuple))
      self.assertEqual(len(bs), 4)

      bs.update(bs2)
      self.assertEqual(len(bs), 5)

      self.assertEqual(bs.setdefault('a'), 1)
      self.assertEqual(bs.setdefault('a', 0), 1)
      del bs['a']
      self.assertEqual(bs.setdefault('a', 0), 0)
      del bs['a']
      self.assertEqual(bs.setdefault('a'), None)

      bs.clear()
      populate_bs(bs, 5)

      bs.close()
      bs2.close()
      bs3.close()

      self.assertTrue(bs.closed())
      with BackingStore(5, 'foo') as bs:
         self.assertEqual(bs['a'], 1)
         self.assertEqual(bs['b'], 2)
         self.assertEqual(bs['c'], 3)
         self.assertEqual(bs['d'], 4)
         self.assertEqual(bs['e'], 5)
         self.assertFalse(bs.closed())
      self.assertTrue(bs.closed())

      with BackingStore(3, 'foo') as bs:
         self.assertEqual(len(bs), 3)

      with self.assertRaises(BStoreClosedError):
         bs2['a']
      with self.assertRaises(BStoreClosedError):
         bs2['a'] = 0
      with self.assertRaises(BStoreClosedError):
         del bs2['a']
      with self.assertRaises(BStoreClosedError):
         iter(bs2)
      with self.assertRaises(BStoreClosedError):
         len(bs2)
      with self.assertRaises(BStoreClosedError):
         'a' in bs2
      with self.assertRaises(BStoreClosedError):
         bs2.keys()
      with self.assertRaises(BStoreClosedError):
         bs2.items()
      with self.assertRaises(BStoreClosedError):
         bs2.values()
      with self.assertRaises(BStoreClosedError):
         bs2.get('a')
      with self.assertRaises(BStoreClosedError):
         bs2.pop('a')
      with self.assertRaises(BStoreClosedError):
         bs2.popitem()
      with self.assertRaises(BStoreClosedError):
         bs2.clear()
      with self.assertRaises(BStoreClosedError):
         bs2.update(bs)
      with self.assertRaises(BStoreClosedError):
         bs2.setdefault('a')

      self.assertEqual(str(bs), 'BackingStore: closed')

      CacheTest.rm_or_noop('foo.db')
      CacheTest.rm_or_noop('bar.db')
      CacheTest.rm_or_noop('baz.db')

   def test_capacity(self):
      with self.assertRaises(ValueError):
         BackingStore(0)
      with self.assertRaises(ValueError):
         Cache(0)

   def test_2_lv_cache_with_bstore(self):
      ct = CacheTest

      ct.rm_or_noop('bstore.db')

      c = Cache(1)
      self.assertTrue(c.bstore_closed())
      self.assertRaises(NoBStoreError, c.open_bstore)

      c2 = Cache(2)
      c = Cache(1, lower_mem=c2)
      self.assertTrue(c.bstore_closed())
      self.assertRaises(NoBStoreError, c.open_bstore)

      bs = BackingStore(3)
      c2 = Cache(2, lower_mem=bs)
      c = Cache(1, lower_mem=c2)

      self.assertTrue(c.bstore_closed())
      c.open_bstore()
      self.assertFalse(c.bstore_closed())
      c.close_bstore()
      self.assertTrue(c.bstore_closed())

      c.open_bstore()
      c['a'] = 1
      c['b'] = 2
      c['c'] = 3
      c['d'] = 4
      c['e'] = 5
      c['f'] = 6
      self.assertEqual(c.items(), [('f', 6)])
      self.assertEqual(c2.items(), [('d', 4), ('e', 5)])
      self.assertEqual(sorted(bs.items()), [('a', 1), ('b', 2), ('c', 3)])

      c['g'] = 7
      self.assertEqual(c.items(), [('g', 7)])
      self.assertEqual(c2.items(), [('e', 5), ('f', 6)])
      self.assertEqual(len(bs), 3)

      exp_str = "cascade dump:\n" +\
           "   Cache: [(g, (True, 7))]\n" +\
           "   Cache: [(e, (True, 5)), (f, (True, 6))]\n" +\
           "   BackingStore: [('a', 1), ('c', 3), ('d', 4)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      bs.clear()
      bs['a'] = 1
      bs['c'] = 3
      bs['d'] = 4

      exp_str = "cascade dump:\n" + \
                "   Cache: [(g, (True, 7))]\n" + \
                "   Cache: [(e, (True, 5)), (f, (True, 6))]\n" + \
                "   BackingStore: [('a', 1), ('c', 3), ('d', 4)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      self.assertEqual(c['g'], 7)
      self.assertEqual(c['e'], 5)
      self.assertEqual(c['f'], 6)
      self.assertEqual(c['a'], 1)

      exp_str = "cascade dump:\n" + \
                "   Cache: [(a, (False, 1))]\n" + \
                "   Cache: [(e, (True, 5)), (f, (True, 6))]\n" + \
                "   BackingStore: [('a', 1), ('c', 3), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['a'] = 2

      exp_str = "cascade dump:\n" + \
                "   Cache: [(a, (True, 2))]\n" + \
                "   Cache: [(e, (True, 5)), (f, (True, 6))]\n" + \
                "   BackingStore: [('a', 1), ('c', 3), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['c']

      exp_str = "cascade dump:\n" + \
                "   Cache: [(c, (False, 3))]\n" + \
                "   Cache: [(f, (True, 6)), (a, (True, 2))]\n" + \
                "   BackingStore: [('c', 3), ('e', 5), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['g']

      exp_str = "cascade dump:\n" + \
                "   Cache: [(g, (False, 7))]\n" + \
                "   Cache: [(a, (True, 2)), (c, (False, 3))]\n" + \
                "   BackingStore: [('c', 3), ('f', 6), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['f']

      exp_str = "cascade dump:\n" + \
                "   Cache: [(f, (True, 6))]\n" + \
                "   Cache: [(c, (False, 3)), (g, (False, 7))]\n" + \
                "   BackingStore: [('a', 2), ('c', 3), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['a']

      exp_str = "cascade dump:\n" + \
                "   Cache: [(a, (False, 2))]\n" + \
                "   Cache: [(g, (False, 7)), (f, (True, 6))]\n" + \
                "   BackingStore: [('a', 2), ('c', 3), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['f'] = 7

      exp_str = "cascade dump:\n" + \
                "   Cache: [(f, (True, 7))]\n" + \
                "   Cache: [(g, (False, 7)), (a, (False, 2))]\n" + \
                "   BackingStore: [('a', 2), ('c', 3), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['a'] = 2

      exp_str = "cascade dump:\n" + \
                "   Cache: [(a, (True, 2))]\n" + \
                "   Cache: [(g, (False, 7)), (f, (True, 7))]\n" + \
                "   BackingStore: [('a', 2), ('c', 3), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      c['c'] = 4

      exp_str = "cascade dump:\n" + \
                "   Cache: [(c, (True, 4))]\n" + \
                "   Cache: [(f, (True, 7)), (a, (True, 2))]\n" + \
                "   BackingStore: [('a', 2), ('c', 3), ('g', 7)]\n"
      self.assertEqual(ct.cascade_dump(c), exp_str)

      bs.clear()
      c.close_bstore()

      c.clear()
      c2.clear()

      self.assertTrue(c.bstore_closed())
      with Cache(1, lower_mem=c2) as c:
         def populate_multilevel_cache(c, len):
            max = len
            for k, v in zip(string.ascii_lowercase[:max], range(1, max + 1)):
               c[k] = v

         self.assertFalse(c.bstore_closed())
         populate_multilevel_cache(c, 6)

         c['d'] = 44
         exp_str = "cascade dump:\n" + \
                   "   Cache: [(d, (True, 44))]\n" + \
                   "   Cache: [(e, (True, 5)), (f, (True, 6))]\n" + \
                   "   BackingStore: [('a', 1), ('b', 2), ('c', 3)]\n"
         self.assertEqual(ct.cascade_dump(c), exp_str)

         c['f'] = 66
         exp_str = "cascade dump:\n" + \
                   "   Cache: [(f, (True, 66))]\n" + \
                   "   Cache: [(e, (True, 5)), (d, (True, 44))]\n" + \
                   "   BackingStore: [('a', 1), ('b', 2), ('c', 3)]\n"
         self.assertEqual(ct.cascade_dump(c), exp_str)

         c['b'] = 22
         exp_str = "cascade dump:\n" + \
                   "   Cache: [(b, (True, 22))]\n" + \
                   "   Cache: [(d, (True, 44)), (f, (True, 66))]\n" + \
                   "   BackingStore: [('b', 2), ('c', 3), ('e', 5)]\n"
         self.assertEqual(ct.cascade_dump(c), exp_str)

         c['c']
         exp_str = "cascade dump:\n" + \
                   "   Cache: [(c, (False, 3))]\n" + \
                   "   Cache: [(f, (True, 66)), (b, (True, 22))]\n" + \
                   "   BackingStore: [('c', 3), ('d', 44), ('e', 5)]\n"
         self.assertEqual(ct.cascade_dump(c), exp_str)

         c['d']
         exp_str = "cascade dump:\n" + \
                   "   Cache: [(d, (False, 44))]\n" + \
                   "   Cache: [(b, (True, 22)), (c, (False, 3))]\n" + \
                   "   BackingStore: [('c', 3), ('d', 44), ('f', 66)]\n"
         self.assertEqual(ct.cascade_dump(c), exp_str)

      self.assertTrue(c.bstore_closed())
      ct.rm_or_noop('bstore.db')

   def test_recommended_usage_example(self):
      CacheTest.rm_or_noop('bstore.db')

      bs = BackingStore(3)
      c2 = Cache(2, lower_mem=bs)
      with Cache(1, lower_mem=c2) as top_cache:
         top_cache['a'] = 1
         top_cache['b'] = 2
         top_cache['c'] = 3
         top_cache['d'] = 4
         top_cache['e'] = 5
         top_cache['f'] = 6
         print(CacheTest.cascade_dump(top_cache))
         some_value = top_cache['d']
         some_value = top_cache['b']
         print(CacheTest.cascade_dump(top_cache))

      CacheTest.rm_or_noop('bstore.db')

if __name__ == '__main__':
   unittest.main()
