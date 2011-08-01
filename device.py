#!/usr/bin/python

import sys
import os
import ConfigParser

if len(sys.argv) != 2:
    print >>sys.stderr, """
    Usage: %s <device>
    """ % sys.argv[0]
    sys.exit(1)

appname, device = sys.argv

root = os.path.dirname(__file__)
devices = ConfigParser.ConfigParser()
devices.read([os.path.join(root, 'doc', 'devices.ini')])

if device not in devices.sections():
    print 'Unknown device:', device
    sys.exit(2)

files_to_update = ['panucci.conf', 'panucci-all.conf']
files_to_update = [os.path.join(root, 'data', x) for x in files_to_update]

def config_from_file(filename):
    parser = ConfigParser.ConfigParser()
    parser.read([filename])
    return parser

parsers = map(config_from_file, files_to_update)

for key, value in devices.items(device):
    for parser in parsers:
        parser.set('options', key, value)

for parser, filename in zip(parsers, files_to_update):
    parser.write(open(filename, 'w'))

