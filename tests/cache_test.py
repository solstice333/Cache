#!/usr/bin/env python3.5
import unittest
from cache import Cache

class CacheTest(unittest.TestCase):
   def setUp(self):
      d = { 'cherry' : 3, 'blueberry' : 1, 'strawberry' : 2 }
      self.c1 = Cache()
      self.c2 = Cache(init_values=d)

   def test_get(self):
      c2 = self.c2
      self.assertEqual(c2['cherry'], 3)
      self.assertEqual(c2['blueberry'], 1)
      self.assertEqual(c2['strawberry'], 2)
      self.assertEqual(len(c2), 3)

if __name__ == '__main__':
   unittest.main()