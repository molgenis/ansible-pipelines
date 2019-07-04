Do NOT use host_vars for specific hosts as this does not work well with jumphosts/proxy servers and dynamic inventories.
Define group_vars and add the host to a group instead.

The only possible exception is an optional

	host_vars/all.yml

which may be used to configure stuff for all hosts.
