#
##
### Check if we need to be sourced.
##
#
# Make sure we do not source this file for SFTP connections, 
# which will terminate instantly when anything that is not a valid FTP command 
# is printed on STDOUT or STDERR. 
# For SFTP connections as well as SLURM jobs the TERM type is dumb, 
# but in the first case there are no SLURM related environment variables defined.
#
# NOTE: when using the --get-user-env=L option for SLURM's sbatch command,
#       various SLURM_* environment variables are not yet available 
#       when the environment is configured and hence when this file is sourced.
#       The only way to make --get-user-env=L work reliably without causing problems with other 'dumb'
#       shells is to check the BASH_EXECUTION_STRING variable which contains the slurm command 
#       used to parse the environment variables from a simulated login.
#       We still also check SLURM_JOB_ID in case a user sources his environment explicitly in a job.
#
if [[ "${TERM}" == 'dumb' ]] && [[ ! "${BASH_EXECUTION_STRING}" =~ 'slurm' ]] && [[ -z "${SLURM_JOB_ID}" ]] && [[ -z "${SOURCE_HPC_ENV}" ]]; then
    return
fi

#
##
### Update HPC environment.
##
#
MY_DIR="$(cd -P "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"
export HPC_ENV_PREFIX="$(dirname "${MY_DIR}")"

#
# SLURM env vars: make sure jobs submitted with sbatch start with a clean environment.
#
export SBATCH_EXPORT='NONE'
export SBATCH_GET_USER_ENV='30L'
# Custom sacct formats:
export SACCT_FORMAT_ID_STATE="User%20,JobID%-13,JobName%25,QOS%16,State,ExitCode"
export SACCT_FORMAT_REQ_ALLOC="Submit,Eligible,Start,End,ReqTRES%25,Timelimit,AllocTRES%25,NodeList,Elapsed,ExitCode"
export SACCT_FORMAT_USED_AVE="AveCPU,AveDiskRead,AveDiskWrite,AvePages,AveRSS,AveVMSize"
export SACCT_FORMAT_USED_MAX="TotalCPU,MaxDiskRead,MaxDiskWrite,MaxPages,MaxRSS,MaxVMSize"
# Default sacct format:
export SACCT_FORMAT="${SACCT_FORMAT_ID_STATE},${SACCT_FORMAT_REQ_ALLOC}"

#
# Apptainer env vars.
#
APPTAINER_BINDPATH="${HPC_ENV_PREFIX}:${HPC_ENV_PREFIX}:ro"
readarray -t my_groups < <(groups | tr ' ' '\n')
for my_group in "${my_groups[@]}"; do
  if [[ -e "/groups/${my_group}" ]]; then
    APPTAINER_BINDPATH="${APPTAINER_BINDPATH},/groups/${my_group}"
  fi
done
export APPTAINER_BINDPATH

#
# EasyBuild env vars.
#
export EASYBUILD_MODULES_TOOL='Lmod'
export EASYBUILD_MODULE_SYNTAX='Lua'
export EASYBUILD_VERIFY_EASYCONFIG_FILENAMES='True'
#
# Enforcing that the EasyConfigs installed for a tool/module in $EBROOT*/easybuild/*.eb
# conform to PEP8 is nice, but it may be tricky to bootstrap EasyBuild with the Python autopep8 module resulting in:
#     ERROR: Failed to parse configuration options: "Python 'autopep8' module required to reformat dumped easyconfigs as requested"
# CentOS repos have a python-pep8 RPM, but pep8 != autopep8 and there is no RPM providing autopep8 out of the box.
#
#export EASYBUILD_DUMP_AUTOPEP8='True'
export EASYBUILD_ENFORCE_CHECKSUMS='True'
export EASYBUILD_MINIMAL_TOOLCHAINS='True'
export EASYBUILD_INSTALLPATH="${HPC_ENV_PREFIX}"
export EASYBUILD_BUILDPATH="${HPC_ENV_PREFIX}/.tmp/easybuild/builds/"
export EASYBUILD_TMP_LOGDIR="${HPC_ENV_PREFIX}/.tmp/easybuild/logs/"
export EASYBUILD_SOURCEPATH="${HPC_ENV_PREFIX}/sources/"
export EASYBUILD_UMASK=002
export EASYBUILD_SET_GID_BIT=1
export EASYBUILD_GROUP_WRITABLE_INSTALLDIR='True'
export TEST_EASYBUILD_MODULES_TOOL='Lmod'
#
# Configure our module tool (Lmod).
#
export PATH=${HPC_ENV_PREFIX}/software/Lua/{{ lua_version }}/bin:$PATH
export PATH=${HPC_ENV_PREFIX}/software/lmod/lmod/libexec:$PATH
source ${HPC_ENV_PREFIX}/software/lmod/lmod/init/bash
export LMOD_CACHE_DIR="${HPC_ENV_PREFIX}/modules/.lmod/cache/"
export LMOD_TIMESTAMP_FILE="${HPC_ENV_PREFIX}/modules/.lmod/modules_changed.timestamp"
export LMOD_RC="${HPC_ENV_PREFIX}/modules/.lmod/lmodrc.lua"
export LMOD_ADMIN_FILE="${HPC_ENV_PREFIX}/modules/modules.admin"
export LMOD_CASE_INDEPENDENT_SORTING='True'
export LMOD_REDIRECT='True'
export LMOD_PAGER='none'
unset MODULEPATH # Make sure Lmod starts with a clean MODULEPATH
if shopt -q login_shell; then
    echo -n "Fetching available environment modules from ${HPC_ENV_PREFIX}/modules/... "
fi
declare module_dirs=''
for module_class in $(ls -1 ${HPC_ENV_PREFIX}/modules/); do
    if [ "${module_class}" != 'all' ] && \
       [ -d ${HPC_ENV_PREFIX}/modules/${module_class}/ ] && \
       [ -r ${HPC_ENV_PREFIX}/modules/${module_class}/ ]; then
        module_dirs="${module_dirs} ${HPC_ENV_PREFIX}/modules/${module_class}/"
    fi
done
module use ${module_dirs}
if shopt -q login_shell; then
    echo ' done!'
fi
