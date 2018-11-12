
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: homsaplog
    type: stdout
    short_description: Homo sapiens friendly formatted output.
    description:
      - Use this callback to sort though extensive debug output
'''

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
from ansible.plugins.callback import CallbackBase

try:
    # Ansible 2.3
    from ansible.vars import strip_internal_keys
except ImportError:
    try:
        # Anisble2.4
        from ansible.vars.manager import strip_internal_keys
    except ImportError:
        # Ansible 2.5
        from ansible.vars.clean import strip_internal_keys

try:
    import simplejson as json
except ImportError:
    import json
import sys
reload(sys).setdefaultencoding('utf-8')

class CallbackModule(CallbackModule_default):  # pylint: disable=too-few-public-methods,no-init
    '''
    Override for the default callback module.

    Render std err/out outside of the rest of the result which it prints with
    indentation.
    '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'homsaplog'

    def _dump_results(self, result, indent=4, sort_keys=True, keep_invocation=False):
        '''Return the text to output for a result.'''

        if result.get('_ansible_no_log', False):
            return json.dumps(dict(censored="The output has been hidden due to the fact that 'no_log: true' was specified for this result."))

        # All result keys starting with _ansible_ are for internal use only, so remove them from the result before we output anything.
        reformatted_result = strip_internal_keys(result)
 
        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
            del reformatted_result['invocation']

        # remove diff information from screen output
        if self._display.verbosity < 3 and 'diff' in result:
            del reformatted_result['diff']
 
        # remove exception from screen output
        if 'exception' in reformatted_result:
            del reformatted_result['exception']
        
        output = json.dumps(reformatted_result, indent=indent, ensure_ascii=False, sort_keys=sort_keys)
        output = output.replace('\\r\\n\",', '",')
        output = output.replace('\\r\\n', "\n\t")
        output = output.replace('\\n\",', '",')
        output = output.replace('\\n', "\n\t")
        return output
