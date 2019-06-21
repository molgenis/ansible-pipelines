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
#       the ${SLURM_JOBID} variable is not yet available when the environment is 
#       configured and hence when this file is sourced. The only way to make 
#       --get-user-env=L work reliably without causing problems with other 'dumb'
#       shells is to make sure the SLURM slurmd daemon is started using a regular 
#       (pseudo) terminal, so ${TERM} won't be 'dumb'.
#
if [ ${TERM} == 'dumb' ] && [ -z ${SLURM_JOBID} ] && [ -z ${SOURCE_HPC_ENV} ]; then
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
# EasyBuild env vars.
#
export EASYBUILD_MODULES_TOOL='Lmod'
export EASYBUILD_MODULE_SYNTAX='Lua'
export EASYBUILD_VERIFY_EASYCONFIG_FILENAMES='True'
#export EASYBUILD_DUMP_AUTOPEP8='True'
export EASYBUILD_INSTALLPATH="${HPC_ENV_PREFIX}"
export EASYBUILD_BUILDPATH="${HPC_ENV_PREFIX}/.tmp/easybuild/builds/"
export EASYBUILD_SOURCEPATH="${HPC_ENV_PREFIX}/sources/"
export EASYBUILD_UMASK=002
export EASYBUILD_SET_GID_BIT=1
export TEST_EASYBUILD_MODULES_TOOL='Lmod'
#
# Configure our module tool (Lmod).
#
export PATH=${HPC_ENV_PREFIX}/software/Lua/{{ lua_version }}/bin:$PATH;
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
echo -n "Fetching available environment modules from ${HPC_ENV_PREFIX}/modules/... "
declare module_dirs=''
for module_class in $(ls -1 ${HPC_ENV_PREFIX}/modules/); do
    if [ "${module_class}" != 'all' ] && \
       [ -d ${HPC_ENV_PREFIX}/modules/${module_class}/ ] && \
       [ -r ${HPC_ENV_PREFIX}/modules/${module_class}/ ]; then
        module_dirs="${module_dirs} ${HPC_ENV_PREFIX}/modules/${module_class}/"
    fi
done
module use ${module_dirs}
echo ' done!'
