#!/usr/bin/env python3.5
import unittest
from cache import Cache
from copy import deepcopy


class CacheTest(unittest.TestCase):
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


if __name__ == '__main__':
   unittest.main()