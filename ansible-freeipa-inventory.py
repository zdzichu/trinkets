#!/usr/bin/python
#
# you may want to install (free)ipa-python package
#
# skeleton provided by Rob Crittenden
# fleshed out by Tomasz Torcz <tomek@pipebreaker.pl>
#

from ipalib import api
from ipalib import errors

import json
import sys


def groups_find(api):
	inventory = {}
	inventory["ungrouped"] = { "hosts" : [] }

	# TODO ask only for fqdn and memberof_hostgroup (attrlist?)
	for host in api.Command["host_find"]()["result"]:
		host_fqdn = host["fqdn"][0]

		try:
			for group in host['memberof_hostgroup']:

				if not group in inventory:
					# first occurence of this group
					inventory[group] = { "hosts" : [] }

				inventory[group]["hosts"].append(host_fqdn)
		except KeyError:
			# no groups
			inventory["ungrouped"]["hosts"].append(host_fqdn)

	print json.dumps(inventory)


def host_find(api, host):
	# we have no specific to pass
	host_vars = {}
	print json.dumps(host_vars)


if __name__ == "__main__":
	api.bootstrap(context='iparest')
	api.finalize()

	api.Backend.xmlclient.connect()

	if len(sys.argv) == 2 and (sys.argv[1] == "--list"):
		groups_find(api)
	elif len(sys.argv) == 3 and (sys.argv[1] == "--host"):
		host_find(api, sys.argv[2])
