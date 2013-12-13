#!/usr/bin/python
#
# you may want to install (free)ipa-python package
#
# skeleton provided by Rob Crittenden
# fleshed out by Tomasz Torcz <tomek@pipebreaker.pl>
#

from ipalib import api
from ipalib import errors

api.bootstrap(context='iparest')
api.finalize()

api.Backend.xmlclient.connect()

print api.Command['host_find']()['result']

