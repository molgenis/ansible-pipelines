#!/usr/bin/python

import json
import sys

from ansible.module_utils.basic import *

changed = True
failed = False

module = AnsibleModule(
    argument_spec={
        'easyconfigs': {'required': True, 'type': 'str'},
        'module': {'default': "EasyBuild", 'required': False, 'type': 'str'},
        'extra_args': {'default': "", 'required': False, 'type': 'str'}
    },
    supports_check_mode=True)

# TODO: Add command constructor

eb_command = "echo eb " + module.params["extra_args"] + " " + module.params["easyconfigs"] + " --help"

(rc, stdout, stderr) =  module.run_command("bash -lc \"set -e; module load " + module.params["module"] + " && " + eb_command + "; exit $?\"")

# TODO: Add check on output if EasyBuild did install something

# Check exit code
if rc != 0: failed = True

print json.dumps({
    "eb_command": eb_command,
    "arguments" : module.params,
    "changed" : changed,
    "failed" : failed,
    "exitcode": rc,
    "stdout": stdout,
    "stderr": stderr
})