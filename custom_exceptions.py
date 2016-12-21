#!/usr/bin/env python3.5

class MaxCapacityError(Exception):
   def __str__(self):
      return "Error: Max capacity reached"
