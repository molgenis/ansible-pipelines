# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Inspired from:
# https://github.com/n0ts/ansible-human_log
# https://github.com/redhat-openstack/khaleesi/blob/master/plugins/callbacks/human_log.py
# Further improved support Ansible 2.0
#

from __future__ import (absolute_import, division, print_function)
import sys
import os
import fcntl
import termios
import struct
reload(sys).setdefaultencoding('utf-8')
try:
    import simplejson as json
except ImportError:
    import json
from ansible.utils.color import stringc
from ansible import constants as AC
from ansible.plugins.callback import CallbackBase

__metaclass__ = type

#
# List of fields for which to reformat output.
#
FIELDS = ['cmd', 'command', 'start', 'end', 'delta', 'msg', 'stdout', 'stderr', 'results', 'changed', 'failed']

class CallbackModule(CallbackBase):
    
    """
    Ansible callback plugin for human-readable result logging
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'human_log'
    CALLBACK_NEEDS_WHITELIST = False
    
    def get_terminal_width(self):
        fcall = fcntl.ioctl(1, termios.TIOCGWINSZ,
                            struct.pack('hhhh', 0, 0, 0, 0))
        term_lines, term_columns = struct.unpack('hhhh', fcall)[:2]
        return term_columns
    
    def human_log(self, data, color):
        self.term_columns = self.get_terminal_width()
        if type(data) == dict:
            #print(str("DEBUG: we've got expected 'data'; it's a dict.\n"))
            #for mykey in data.keys():
                #print(str("DEBUG: 'data' has key {0}.\n".format(mykey)))
            for field in FIELDS:
                #print(str("DEBUG: processing field: {0}.\n".format(field)))
                no_log = data.get('_ansible_no_log')
                if field in data.keys() and data[field] and no_log is not True:
                    output = self._format_output(data[field])
                    print(str(stringc("\n{0}: {1}".format(field, output.replace("\\n", "\n")), color)))
        else:
            print(str("ERROR: we've got unexpected 'data'.\n"))
    
    def _format_output(self, output):
        # Strip Unicode
        #if type(output) == unicode:
        #    output = output.encode(sys.getdefaultencoding(), 'replace')
        #
        # If output is a dict.
        #
        if type(output) == dict:
            #print(str("DEBUG: we've got a dict.\n"))
            return json.dumps(output, indent=2)
        #
        # If output is a list of dicts.
        #
        elif type(output) == list and type(output[0]) == dict:
            #print(str("DEBUG: we've got a list of dicts.\n"))
            # This gets a little complicated because it potentially means
            # nested results, usually because of with_items.
            #print(str("DEBUG: we've got items.\n"))
            real_output = list()
            for index, item in enumerate(output):
                copy = item
                if type(item) == dict:
                    for field in FIELDS:
                        if field in item.keys():
                            copy[field] = self._format_output(item[field])
                real_output.append(copy)
            return json.dumps(output, indent=2)
        #
        # If output is a list of strings.
        #
        elif type(output) == list and type(output[0]) != dict:
            #print(str("DEBUG: we've got a list of non dicts.\n"))
            # Strip newline characters
            real_output = list()
            for item in output:
                if "\n" in item:
                    for string in item.split("\n"):
                        real_output.append(string)
                else:
                    real_output.append(item)
            #
            # Reformat lists with line breaks,
            # but only if line length > the terminal width.
            #
            if len("".join(real_output)) > self.term_columns:
                return "\n" + "\n".join(real_output)
            else:
                return " ".join(real_output)
        else:
            #
            # I's a string, (or an int, float, etc.) just return it.
            #
            #print(str("DEBUG: we've got nothing special.\n"))
            return str(output)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.human_log(res, AC.COLOR_ERROR)

    def runner_on_ok(self, host, res):
        if res.pop('changed', False):
            self.human_log(res, AC.COLOR_CHANGED)
        else:
            pass

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        self.human_log(res, AC.COLOR_UNREACHABLE)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        self.human_log(res, AC.COLOR_VERBOSE)

    def runner_on_async_ok(self, host, res, jid):
        if res.pop('changed', False):
            self.human_log(res, AC.COLOR_CHANGED)
        else:
            pass

    def runner_on_async_failed(self, host, res, jid):
        self.human_log(res, AC.COLOR_ERROR)

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, name):
        pass

    def playbook_on_stats(self, stats):
        pass

    def on_file_diff(self, host, diff):
        pass

    #
    # V2 METHODS
    #
    def v2_on_any(self, *args, **kwargs):
        pass

    def v2_runner_on_failed(self, result, ignore_errors=False):
        #print(str("DEBUG: triggered v2_runner_on_failed.\n"))
        self.human_log(result._result, AC.COLOR_ERROR)

    def v2_runner_on_ok(self, result):
        #self.human_log(result._result, AC.COLOR_OK)
        if result._result.pop('changed', False):
            self.human_log(result._result, AC.COLOR_CHANGED)
        else:
            pass

    def v2_runner_on_skipped(self, result):
        pass

    def v2_runner_on_unreachable(self, result):
        self.human_log(result._result, AC.COLOR_UNREACHABLE)

    def v2_runner_on_no_hosts(self, task):
        pass

    def v2_runner_on_async_poll(self, result):
        self.human_log(result._result, AC.COLOR_DEBUG)

    def v2_runner_on_async_ok(self, host, result):
        #self.human_log(result._result, AC.COLOR_OK)
        if result.pop('changed', False):
            self.human_log(result._result, AC.COLOR_CHANGED)
        else:
            pass

    def v2_runner_on_async_failed(self, result):
        #print(str("DEBUG: triggered  v2_runner_on_async_failed.\n"))
        self.human_log(result._result, AC.COLOR_ERROR)

    def v2_playbook_on_start(self, playbook):
        pass

    def v2_playbook_on_notify(self, result, handler):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        pass

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                   encrypt=None, confirm=False, salt_size=None,
                                   salt=None, default=None):
        pass

    def v2_playbook_on_setup(self):
        pass

    def v2_playbook_on_import_for_host(self, result, imported_file):
        pass

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        pass

    def v2_playbook_on_play_start(self, play):
        pass

    def v2_playbook_on_stats(self, stats):
        pass

    def v2_on_file_diff(self, result):
        pass

    def v2_playbook_on_item_ok(self, result):
        pass

    def v2_playbook_on_item_failed(self, result):
        #print(str("DEBUG: triggered v2_playbook_on_item_failed.\n"))
        self.human_log(result._result, AC.COLOR_ERROR)
        #pass

    def v2_playbook_on_item_skipped(self, result):
        pass

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_item_on_ok(self, result):
        pass

    def v2_playbook_item_on_failed(self, result):
        #print(str("DEBUG: v2_playbook_item_on_failed.\n"))
        self.human_log(result._result, AC.COLOR_ERROR)
        #pass

    def v2_playbook_item_on_skipped(self, result):
        pass
