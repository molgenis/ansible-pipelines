#!/usr/bin/env python

'''
=============================================================
External inventory script for Ansible
=============================================================

Generates Ansible inventory with hostnames from a static inventory file located
in the same dir as this script. By default this script looks for an inventory named
    inventory.ini
or alternatively for an inventory file name as defined in
    export AI_INVENTORY='some_inventory.ini'

The hostnames parsed from the static inventory file can be prefixed
with the hostname of one of our proxy/jumphost servers.
Note we only use hostnames and not FQDN nor IP addresses as those are managed
together with usernames and other connection settings in
our ~/.ssh/config files like this:

########################################################################################################
#
# HPC hosts.
#
Host lobby foyer *calculon *boxy !*.hpc.rug.nl
    HostName %h.hpc.rug.nl
    User prefix-youraccount
#
# Proxy settings.
#
Host lobby+* foyer+* airlock+*
    PasswordAuthentication No
    ProxyCommand ssh -X -q prefix-youraccount@$(echo %h | sed 's/+[^+]*$//').hpc.rug.nl -W $(echo %h | sed 's/^[^+]*+//'):%p
########################################################################################################

When the environment variable AI_PROXY is set like this:
    export AI_PROXY='lobby'
then the hostname 'calculon' from inventory.ini will be prefixed
with 'lobby' and a '+' resulting in:
    lobby+calculon
which will match the 'Host lobby+*' rule from the ~/.ssh/config file.
=============================================================
'''
import argparse
#try:
#    # For Python >= 3.x
#    import configparser
#except:
#    # For Python 2.x
#    import ConfigParser as configparser
try:
    import json
except ImportError:
    import simplejson as json
import os
import re
import sys
from test.test_sax import start
if sys.version_info >= (3,2,0):
    from configparser import ConfigParser
elif sys.version_info >= (3,0,0):
    from configparser import SafeConfigParser as ConfigParser
else:
    # For Python 2.x
    from ConfigParser import SafeConfigParser as ConfigParser

"""
Modified ConfigParser that allows ':' in keys and only uses '=' as separator.
We need the : to be able to specify groups of Ansible hosts like this: compute_nodes[01:16]
"""
cp_classname = 'SafeConfigParser'
if sys.version_info >= (3,2,0):
    cp_classname = 'ConfigParser'

#class MyConfigParser(configparser.SafeConfigParser):
class MyConfigParser(ConfigParser):
    OPTCRE = re.compile(
        r'(?P<option>[^=\s][^=]*)'      # very permissive!
        r'\s*(?P<vi>[=])\s*'            # any number of space/tab,
                                        # followed by separator
                                        # (either : or =), followed
                                        # by any # space/tab
        r'(?P<value>.*)$'               # everything up to eol
        )
    OPTCRE_NV = re.compile(
        r'(?P<option>[^=\s][^=]*)'      # very permissive!
        r'\s*(?:'                       # any number of space/tab,
        r'(?P<vi>[=])\s*'               # optionally followed by
                                        # separator (only =)
                                        # followed by any #
                                        # space/tab
        r'(?P<value>.*))?$'             # everything up to eol
)

class ProxiedInventory(object):

    def __init__(self):

        # A list of groups and the hosts in that group.
        self.inventory = dict()

        # Get proxy from ENV VAR.
        self.proxy = '' # default when not specified.
        self.proxy = os.getenv('AI_PROXY')

        # Get inventory file name from ENV VAR.
        self.inventory_file = os.getenv('AI_INVENTORY')
        if not self.inventory_file:
            self.inventory_file = 'inventory.ini'
        self.inventory_path = os.path.dirname(os.path.realpath(__file__)) + '/' + self.inventory_file
        if not (os.path.isfile(self.inventory_path) and os.access(self.inventory_path, os.R_OK)):
            print('FATAL: The static inventory file ' + self.inventory_path + "\n"
                  '       is either missing or not readable: Check path and permissions.\n' +
                  '       If your static inventory file has a different name,\n' +
                  '       you need to export the AI_INVENTORY environment variable\n' +
                  '       to point to a static inventory file in the same dir as where\n' +
                  '           ' + os.path.realpath(__file__) + "\n" +
                  '       is located.')
            sys.exit(1)

        # Read settings and parse CLI arguments.
        self.read_inventory_template()
        self.parse_cli_args()

        data_to_print = ""
        data_to_print += self.dict_to_json(self.inventory, True)
        print(data_to_print)

    def read_inventory_template(self):
        """
        Read the inventory details from an Ansible inventory file
         * named 'inventory',
         * in *.ini format and
         located in the same place as this script.
        """
        #_config = ConfigParser.SafeConfigParser(allow_no_value=True)
        #_config.optionxform = self.prepend_proxy
        _config = MyConfigParser(allow_no_value=True)
        _config.read(os.path.dirname(os.path.realpath(__file__)) + '/' + self.inventory_file)
        
        #
        # This dynamic inventory script does not (yet) support execution with a --host argument to get the hostvars for an inventory item.
        # From: https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#script-conventions
        # To satisfy the requirements of using _meta, to prevent ansible from calling your inventory with --host you must at least populate _meta with an empty hostvars dictionary.
        #
        _meta = dict()
        _hostvars = dict()
        self.add(_meta, 'hostvars', _hostvars)
        self.add(self.inventory, '_meta', _meta)
        
        for _section in _config.sections():
            if re.search(':children', _section):
                #
                # We've got groups of machines instead of hostnames:
                #  * Do not prefix values with name of proxy/jumphost
                #  * and add them to a "children" section
                #
                #self.push(self.inventory, _section, _key)
                _children = dict()
                for (_key, _value) in _config.items(_section):
                    self.push(_children, 'children', _key)
                _section = _section.replace(':children', '')
                self.add(self.inventory, _section, _children)
            else:
                #
                # We've got actual machine hostnames:
                #  * Prefix with name of proxy/jumphost unless it is the proxy/jumphost itself
                #  * and add them to a 'hosts' section.
                #
                _hosts = dict()
                for (_key, _value) in _config.items(_section):
                    if _key != self.proxy:
                        _key = self.prepend_proxy(_key)
                    #
                    # Check if we are dealing with a range or a single hostname.
                    #
                    _range_match = re.search('(.*)\[([0-9]+):([0-9]+)\](.*)', _key)
                    if _range_match:
                        #
                        # It's a range -> expand the range into individual hostnames
                        # and add them to the hosts section.
                        #
                        _pre_range = _range_match.group(1)
                        _range_start = _range_match.group(2)
                        _range_stop = _range_match.group(3)
                        _post_range = _range_match.group(4)
                        _range_start_length = len(_range_start)
                        _format = '{:0' + str(_range_start_length) + 'd}'
                        _range_items = [_format.format(i) for i in range(int(_range_start),int(_range_stop) + 1)]
                        for _range_item in _range_items:
                            self.push(_hosts, 'hosts', _pre_range + _range_item + _post_range)
                    else:
                        #
                        # Add the single hostname to the hosts section.
                        #
                        self.push(_hosts, 'hosts', _key)
                self.add(self.inventory, _section, _hosts)

    def prepend_proxy(self, _string):
        """
        Prepends proxy before host.
        """
        return re.sub('^', self.proxy + '+', _string)

    def parse_cli_args(self):
        """
        Process command line arguments.
        """
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file.')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        self.args = parser.parse_args()

    def push(self, _dict, _key, _element):
        """
        Push an element into an array that may or may not have been defined already in the dict.
        """
        if _key in _dict:
            _dict[_key].append(_element)
        else:
            _dict[_key] = [_element]

    def add(self, _dict, _key, _element):
        """
        Add a key to a dict.
        """
        _dict[_key] = _element

    def dict_to_json(self, _data, _pretty=False):
        """
        Convert a dict into a string in JSON format.
        """
        if _pretty:
            return json.dumps(_data, sort_keys=True, indent=2)
        else:
            return json.dumps(_data)

#
# Main
#
if __name__ == "__main__":
    ProxiedInventory()
