# ansible-pipelines

[![CircleCI](https://circleci.com/gh/molgenis/ansible-pipelines/tree/master.svg?style=svg)](https://circleci.com/gh/molgenis/ansible-pipelines/tree/master)

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
   - Configure the Bash environment for Lmod & EasyBuild
   - Create the basic file system layout for processing a project with various pipelines for various groups.
   - Create cronjobs for running pipelines automatically for functional accounts of various groups.

## Prerequisites for pipeline deployment

 - On the managing computer Ansible 2.2.x or higher is required to run the playbook.
 - The playbook was tested on target servers running CentOS >= 7 and similar Linux distro from the ''RedHat'' family.
   When deploying on other Linux distro's the playbook may need updates for differences in package naming.
 - A basic understanding of Ansible (See: http://docs.ansible.com/ansible/latest/intro_getting_started.html#)
 - A basic understanding of EasyBuild not required to deploy the pipeline ''as is'', but will come in handy when updating/modifying the pipeline and it's dependencies.

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

The default values for variables (like the version numbers of tools to install, URLs for their sources and checksums) are stored in:
```
group_vars/all
```
When you need to override any of the defaults, then create a file with the name of a group as listed in the inventory in:
```
group_vars/[stack_name]
```
You don't need to list all variables in the file in ```group_vars/```, but only the ones for which you need a different value.

IMPORTANT: Do not use ```host_vars``` as that does not work well with the dynamic inventory (see below) when working with jumphosts to reach a target server.
When a jumphost is used and its name is prefixed in front of the name of the target host, then the combined "hostname" will no longer match files or directories in ```host_vars```.
Hence you should
 * either assign the destination host to a group and use ```group_vars``` even when the group contains only a single host.
 * or alternatively you can add host specific variables to machines listed in the *static inventory file* for a *stack*.

## Dynamic vs. static inventory

 - ```static_inventories/[stack_name].yml```: is a static inventory file.
 - ```inventory_plugins/yaml_with_jumphost.py```: is an Ansible inventory plugin to generate dynamic inventories based on a static one.

The dynamic inventory plugin uses the environment variables ```AI_PROXY``` and ```ANSIBLE_INVENTORY``` and will 
prefix all hostnames listed in the static inventory with the name of the specified proxy/jumphost server. E.g.

The static inventory files should not contain SSH connection settings / parameters like port numbers, usernames, expansion of aliases/hostnames to fully qualified domain names (FQDNs), etc.
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
# Proxy/jumphost settings.
#
Host some_proxy+*
    ProxyCommand ssh -X -q youraccount@some_proxy.my.domain -W $(echo %h | sed 's/^some_proxy[^+]*+//'):%p
Host other_proxy+*
    ProxyCommand ssh -X -q youraccount@other_proxy.my.domain -W $(echo %h | sed 's/^other_proxy[^+]*+//'):%p
########################################################################################################
```

When the environment variables are set like this:
```bash
export AI_PROXY='other_proxy'
export ANSIBLE_INVENTORY='static_inventories/my_cluster_stack.yml'
```
then the hostname ```some_target``` from a ```static_inventories/my_cluster_stack.yml``` file will be prefixed with ```other_proxy``` and a '+'
resulting in:
```bash
other_proxy+some_target
```
which will match the ```Host other_proxy+*``` rule from the example ```~/.ssh/config``` file.

Setting the ```AI_PROXY``` and ```ANSIBLE_INVENTORY``` environment variables can also be accomplished with less typing
by sourcing an initialisation file, which provides the ```repo-config``` function
to configure these environment variables for a specific *stack*:
```bash
. ./repo-init
repo-config [stack_prefix]
```

## Deployment: running the playbook

#### 0. Fork this repo.

Firstly, fork the repo at GitHub. Consult the GitHub docs if necessary.

#### 1. Clone forked repo to Ansible control host.

Login to the machine you want to use as Ansible control host, clone your fork and add "blessed" remote:

```bash
mkdir -p ${HOME}/git/
cd ${HOME}/git/
git clone 'https://github.com/<your-github-account>/ansible-pipelines.git'
cd ${HOME}/git/ansible-pipelines
git remote add blessed 'https://github.com/molgenis/ansible-pipelines.git'
```

#### 2. Configure Python virtual environment.

Login to the machine you want to use as Ansible control host and configure virtual Python environment in sub directory of your cloned repo:

```bash
export REPO_HOME="${HOME}/git/ansible-pipelines"
cd "${REPO_HOME}"
#
# Create Python virtual environment (once)
#
python3 -m venv "${REPO_HOME}/ansible.venv"
#
# Activate virtual environment.
#
source "${REPO_HOME}/ansible.venv/bin/activate"
#
# Install Ansible and other python packages.
#
if command -v pip3 > /dev/null 2>&1; then
    PIP=pip3
elif command -v pip > /dev/null 2>&1; then
    PIP=pip
else
    echo 'FATAL: Cannot find pip3 nor pip. Make sure pip(3) is installed.'
fi
${PIP} install --upgrade pip
${PIP} install 'ansible<12' # For running playbooks on your local laptop as Ansible control host.
${PIP} install 'ansible<6' # For running playbooks directly on chaperone machines running RHEL8.
${PIP} install jmespath
${PIP} install ruamel.yaml
#
# Optional: install Mitogen with pip.
# Mitogen provides an optional strategy plugin that makes playbooks a lot (up to 7 times!) faster.
# See https://mitogen.networkgenomics.com/ansible_detailed.html
#
${PIP} install mitogen
#
# Configure the Ansible vault password to decrypt encrypted content.
#
mkdir -m 700 "${REPO_HOME}/.vault"
touch "${REPO_HOME}/.vault/vault_pass.txt.all"
chmod 600 "${REPO_HOME}/.vault/vault_pass.txt.all"
#
# Use your favorite text editor to add the vault password to ${REPO_HOME}.vault/vault_pass.txt.all
#
```

#### 3A. Run playbook on Ansible control host for *-chaperone machines

* Only for: machines in the *chaperone* inventory group.
* First time only: ssh to the `ansible-host` from static-inventory yml (e.g. static_inventories/copperfist_cluster.yml)
* Use `localhost` as the *Ansible control host*; hence run the playbook on the `chaperone` itself.

Login to the Ansible control host and:

```bash
export REPO_HOME="${HOME}/git/ansible-pipelines"
cd "${REPO_HOME}"
#
# Make sure we are on the main branch and got all the latest updates.
#
git checkout master
git pull blessed master
#
# Activate virtual environment.
#
source "${REPO_HOME}/ansible.venv/bin/activate"
source "${REPO_HOME}/repo-init"
repo-config [stack_prefix]  # Stack prefix as defined in group_vars/stack_name/vars.yml. E.g. bb, cf or wh.
#
# Run complete playbook: example for wh-chaperone
#
repo-config wh
ansible-playbook --limit 'chaperone' playbook.yml
#
# Run single role playbook: examples for wh-chaperone
#
repo-config wh
ansible-playbook --limit 'chaperone' single_role_playbooks/install_easybuild.yml
ansible-playbook --limit 'chaperone' single_role_playbooks/fetch_extra_easyconfigs.yml
ansible-playbook --limit 'chaperone' single_role_playbooks/install_modules_with_easybuild.yml
ansible-playbook --limit 'chaperone' single_role_playbooks/create_group_subfolder_structure.yml
ansible-playbook --limit 'chaperone' single_role_playbooks/manage_cronjobs.yml
```

#### 3B. Run playbook on Ansible control host for all other infra

* For all HPC clusters __*except*__ machines in the *chaperone* inventory group.
* Use your own laptop/device as *Ansible control host*.

Login to the Ansible control host and:

```bash
export REPO_HOME="${HOME}/git/ansible-pipelines"
cd "${REPO_HOME}"
#
# Make sure we are on the main branch and got all the latest updates.
#
git checkout master
git pull blessed master
#
# Activate virtual environment.
#
source "${REPO_HOME}/ansible.venv/bin/activate"
source "${REPO_HOME}/repo-init"
repo-config [stack_prefix]  # Stack prefix as defined in group_vars/stack_name/vars.yml. E.g. gs, tl, bb, cf or wh.
#
# Run complete playbook: example for WingedHelix excluding wh-chaperone
#
repo-config wh
ansible-playbook --limit '!chaperone' playbook.yml
#
# Run single role playbook: examples for WingedHelix excluding wh-chaperone
# Exclude machines in the chaperone inventory group,
# which are only accessible from UMCG network.
#
repo-config wh
ansible-playbook --limit '!chaperone' single_role_playbooks/install_easybuild.yml
ansible-playbook --limit '!chaperone' single_role_playbooks/fetch_extra_easyconfigs.yml
ansible-playbook --limit '!chaperone' single_role_playbooks/fetch_sources_and_refdata.yml
ansible-playbook --limit '!chaperone' single_role_playbooks/install_modules_with_easybuild.yml
ansible-playbook --limit '!chaperone' single_role_playbooks/create_group_subfolder_structure.yml
ansible-playbook --limit '!chaperone' single_role_playbooks/manage_cronjobs.yml
```

## Changing cronjobs in case of (un)scheduled maintenance

In the default situation:
 * Samplesheets from _Darwin_ on `dat05` share/mount:
   * sequencer/scanner must store data on `betabarrel`
   * results are stored on `prm05` share/mount
 * Samplesheets from _Darwin_ on `dat06` share/mount:
   * sequencer/scanner must store data on `copperfist`
   * results are stored on `prm06` share/mount
 * Samplesheets from _Darwin_ on `dat07` share/mount:
   * sequencer/scanner must store data on `wingedhelix`
   * results are stored on `prm07` share/mount

If an infra stack is offline for (un)scheduled maintenance,
the lab can use the other set of infra stack by simply saving the rawest data on one of the other shares and
asking Darwin to put the samplesheet on the corresponding other `dat` share.
In this case there is no need to change any cronjob settings.

If an infra stack breaks down and we need to temporarily disable cronjobs to prevent that infra stack from processing data:
 * Look for the `cronjobs` variable in both `group_vars/[stack_name]/vars.yml`.
 * Temporarily disable a cronjob by adding `disabled: true`. E.g.:
     ```
     - name: NGS_Automated_copyRawDataToPrm_inhouse  # Unique ID required to update existing cronjob: do not modify.
       user: umcg-atd-dm
       machines: "{{ groups['chaperone'] | default([]) }}"
       minute: '*/10'
       job: /bin/bash -c "{{ configure_env_in_cronjob }};
            module load NGS_Automated/{{ group_module_versions['umcg-atd']['NGS_Automated'] }}-bare;
            copyRawDataToPrm.sh -g umcg-atd -p NGS_Demultiplexing -s {{ groups['jumphost'] | first }}+{{ groups['user_interface'] | first }}"
       disabled: true
     ```
 * Run the playbook to update the cronjobs.
