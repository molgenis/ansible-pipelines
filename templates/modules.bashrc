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
echo -n "Fetching available environment modules from ${HPC_ENV_PREFIX}/modules/... "
#
# EasyBuild env vars.
#
export EASYBUILD_MODULES_TOOL='Lmod'
export EASYBUILD_MODULE_SYNTAX='Lua'
export EASYBUILD_INSTALLPATH="${HPC_ENV_PREFIX}"
export EASYBUILD_BUILDPATH="${HPC_ENV_PREFIX}/.tmp/easybuild/builds/"
export EASYBUILD_SOURCEPATH="${HPC_ENV_PREFIX}/sources/"
export EASYBUILD_UMASK=002
export EASYBUILD_SET_GID_BIT=1
export EASYBUILD_STICKY_BIT=1
export TEST_EASYBUILD_MODULES_TOOL='Lmod'
#
# Configure our module tool (Lmod).
#
export PATH="/usr/share/lmod/lmod/libexec/:${PATH}"
export LMOD_CACHE_DIR="${HPC_ENV_PREFIX}/modules/.lmod/cache/"
export LMOD_TIMESTAMP_FILE="${HPC_ENV_PREFIX}/modules/.lmod/modules_changed.timestamp"
export LMOD_RC="${HPC_ENV_PREFIX}/modules/.lmod/lmodrc.lua"
export LMOD_ADMIN_FILE="${HPC_ENV_PREFIX}/modules/modules.admin"
export LMOD_CASE_INDEPENDENT_SORTING='True'
export LMOD_REDIRECT='True'
export LMOD_PAGER='none'
for module_class in $(ls -1 ${HPC_ENV_PREFIX}/modules/); do
    if [ "${module_class}" != 'all' ] && \
       [ -d ${HPC_ENV_PREFIX}/modules/${module_class}/ ] && \
       [ -r ${HPC_ENV_PREFIX}/modules/${module_class}/ ]; then
        module use ${HPC_ENV_PREFIX}/modules/${module_class}/
    fi
done
echo 'done!'
