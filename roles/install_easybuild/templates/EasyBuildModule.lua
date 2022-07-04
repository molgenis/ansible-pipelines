help([==[

Description
===========
EasyBuild is a software build and installation framework
written in Python that allows you to install software in a structured,
repeatable and robust way.


More information
================
 - Homepage: http://easybuilders.github.com/easybuild/
]==])

whatis([==[Description: EasyBuild is a software build and installation framework
written in Python that allows you to install software in a structured,
repeatable and robust way.]==])
whatis([==[Homepage: http://easybuilders.github.com/easybuild/]==])
whatis([==[URL: http://easybuilders.github.com/easybuild/]==])

local root = "{{ easybuild_software_dir }}/EasyBuild/{{ easybuild_version }}"

conflict("EasyBuild")

prepend_path("CMAKE_PREFIX_PATH", root)
prepend_path("PATH", pathJoin(root, "bin"))
setenv("EBROOTEASYBUILD", root)
setenv("EBVERSIONEASYBUILD", "{{ easybuild_version }}")
setenv("EBDEVELEASYBUILD", pathJoin(root, "easybuild/EasyBuild-{{ easybuild_version }}-easybuild-devel"))

prepend_path("PYTHONPATH", pathJoin(root, "{{ pythonpath.stdout }}"))
-- Deployed with Ansible
