#!/usr/bin/env python3.5
import unittest
from cache import Cache
from custom_exceptions import *

class CacheTest(unittest.TestCase):
   def setUp(self):
      d = { 'cherry' : 3, 'blueberry' : 1, 'strawberry' : 2 }
      self.c1 = Cache()
      self.c2 = Cache(init_values=sorted(d.items()))

   def test_get(self):
      c2 = self.c2
      self.assertEqual(c2['cherry'], 3)
      self.assertEqual(c2['blueberry'], 1)
      self.assertEqual(c2['strawberry'], 2)
      self.assertEqual(len(c2), 3)

      print(c2)
      c2['blueberry'] = 3
      print(c2)

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

   def test_str(self):
      self.assertEqual(str(self.c2),
                       'Cache: OrderedDict([('
                       '\'blueberry\', 1), '
                       '(\'cherry\', 3), '
                       '(\'strawberry\', 2)])')

if __name__ == '__main__':
   unittest.main()