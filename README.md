# ansible-pipelines

## Automagic deployment of pipelines for analysis of Next Generation Sequencing data

This repo contains an Ansible playbook for deploying various pipelines for analysis of Next Generation Sequencing data:
 - [NGS_DNA](https://github.com/molgenis/NGS_DNA): pipeline developed originally used for the BBMRI Genome of the Netherlands (GoNL) project.
   The NGS_DNA pipeline was further developed @ UMCG where it is used for regular production work.
 - [NGS_Automated](https://github.com/molgenis/NGS_Automated): Automation for the above, but tailored to infra @ UMCG and RUG.

The deployment consists of the following steps:
 - Use Ansible to:
   - Deploy [Lmod - the Lua based module system](https://github.com/TACC/Lmod)
   - Deploy [EasyBuild](https://github.com/easybuilders/easybuild-easyconfigs)
   - Download and unpack reference data
   - Use EasyBuild to install software for analysis of NGS data. EasyBuild will:
     - Fetch sources
     - Unpack the sources
     - Patch sources
     - Configure
     - Compile/Build
     - Install
     - Run sanity check
     - Create module file for module system of your choice (Lmod in our case).
   - Create the basic file system layout for processing a project with the NGS_DNA pipeline.
   - Configure the Bash environment for Lmod & EasyBuild

## Prerequisites for pipeline deployment

 - On the managing computer Ansible 2.2.x or higher is required to run the playbook.
 - The playbook was tested on target servers running CentOS 6 and similar Linux distro from the ''RedHat'' family.
   When deploying on other Linux distro's the playbook may need updates for differences in package naming.
 - A basic understanding of Ansible (See: http://docs.ansible.com/ansible/latest/intro_getting_started.html#)
 - A basic understanding of EasyBuild not required to deploy the pipeline ''as is'', but will come in handy when updating/modifying the pipeline and it's dependencies.

#### Ansible & environment patches

Various parts of the Ansible playbook use rsync to copy data to the target host.
Unfortunately the Ansible rsync wrapper module contains a few bugs.
These bugs must be patched on the control host:

 - [Bugfix #33998 for bug #17492: Do not prepend PWD when path is in form user@server:path or server:path](https://github.com/ansible/ansible/pull/33998)
 - [Bugfix #41332 for bug #24365: Do not disable SSH connection sharing](https://github.com/ansible/ansible/pull/41332)
possible location for the synchronize script is:
/usr/local/Cellar/ansible/2.4.3.0/libexec/lib/python2.7/site-packages/ansible/modules/files/synchronize.py 


In addition you must add to ```~/.ssh/config``` on the target host from the inventory and for the user running the playbook:
```
#
# Generic stuff: prevent timeouts 
#
Host *
	ServerAliveInterval 60
	ServerAliveCountMax 5

#
# Generic stuff: share existing connections to reduce lag when logging into the same host in a second shell
#
ControlMaster auto
ControlPath ~/.ssh/tmp/%h_%p_%r
ControlPersist 5m
```

## Prerequisites for running the pipeline

 - A basic understanding of how Linux clusters work.
   The Molgenis Compute framework used to generate scripts, 
   which can be submitted to the cluster's scheduler, 
   can support multiple schedulers.
   It comes out-of-the box with templates for Slurm and PBS/Torque.
 - Illumina data from human samples.
   - When you have data from a different sequencing platform you may need to tweak analysis steps.
   - When you have data from a different species you will need to modify the playbook to provision reference data for that species.
   
## Defaults and how to overrule them

The default values for variables (like the version number of the pipeline to deploy) are stored in:
```
group_vars/all
```
When you need to override any of the defaults, then create a file with the name of a host or group as listed in the inventory in:
```
host_vars/[hostname|groupname]
```
You don't need to list all variables in the file in ```host_vars/```, but only the ones for which you need a different value.

## Dynamic vs. static inventory

 - ```inventory.ini```: is the static inventory file.
 - ```inventory.py```: is the dynamic inventory script.

The dynamic inventory script one uses the environment variable ```AI_PROXY``` and when set prefixes the name of the specified proxy server in front of the hostnames listed in the static inventory.
The inventory files handle only (groups of) hostnames.
Hence the inventory files do not list any other SSH connection settings / parameters like port numbers, usernames, expansion of aliases/hostnames to fully qualified domain names (FQDNs), etc.
All SSH connection settings must be stored in your ```~/.ssh/config``` file. An example ```~/.ssh/config``` could look like this:

```
########################################################################################################
#
# Hosts.
#
Host some_proxy other_proxy *some_target *another_target !*.my.domain
    HostName %h.my.domain
    User youraccount
#
# Proxy settings.
#
Host some_proxy+*
    ProxyCommand ssh -X -q youraccount@some_proxy.my.domain -W $(echo %h | sed 's/^some_proxy[^+]*+//'):%p
Host other_proxy+*
    ProxyCommand ssh -X -q youraccount@other_proxy.my.domain -W $(echo %h | sed 's/^other_proxy[^+]*+//'):%p
########################################################################################################
```

When the environment variable ```AI_PROXY``` is set like this:
```
export AI_PROXY='other_proxy'
```
then the hostname ```some_target``` from inventory.ini will be prefixed with ```other_proxy``` and a '+'
resulting in:
```
other_proxy+some_target
```
which will match the ```Host other_proxy+*``` rule from the example ```~/.ssh/config``` file.

## Deployment: running the playbook

Some examples:
 - To list the hosts that will be targeted in a group; e.g. 'development'
   ```
   ansible-playbook -i inventory.py --list-hosts playbook.yml
   ```
 - To run playbook for host 'boxy-dev' accessed via proxy server 'lobby'
   ```
   ansible-playbook -i inventory.py -l lobby+boxy-dev playbook.yml
   ```
 - To debug a playbook for host 'boxy-dev' accessed via proxy server 'lobby' starting somehere in the middle of the playbook as opposed to starting from scratch.
   ```
   ansible-playbook -i inventory.py -l lobby+boxy-dev playbook.yml --start-at-task 'Get EasyConfigs.'
   ```


