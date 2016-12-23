#!/usr/bin/env python3.5
import unittest
from cache import Cache
from cache import CacheMiss
from copy import deepcopy


class CacheTest(unittest.TestCase):
   @staticmethod
   def dump_caches(cache):
      mem = cache
      print("cache dump:")

      while mem is not None:
         print("  {}".format(mem))
         mem = mem.lower_mem

   def setUp(self):
      d = {'cherry':3, 'blueberry':1, 'strawberry':2}
      self.c1 = Cache()
      self.c2 = Cache(init_values=sorted(d.items()))
      self.c3 = Cache(init_values=[('foo',1),('bar',2)])
      self.c4 = Cache(init_values={'a':1, 'b':2})

      self.assertRaises(TypeError, Cache, init_values='foo')

   def test_foo(self):
      print(self.c2)

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

if __name__ == '__main__':
   unittest.main()