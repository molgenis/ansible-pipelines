#!/usr/bin/env python
class FilterModule(object):
  def filters(self):
    return { 'subsetattrs': self.subsetattrs }

  def subsetattrs(self, unfiltered_dict, list_of_keys):
    filtered_dict = {}
    for key in list_of_keys:
      if unfiltered_dict.get(key, None) != None:
        filtered_dict[key] = unfiltered_dict[key]
    return filtered_dict
