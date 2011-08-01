#!/usr/bin/env python

# Usage: device.py <device name>

import sys
import os

bin_dir = os.path.dirname(sys.argv[0])
_device = sys.argv[1]

_file = open(bin_dir + "doc/devices.txt")
_str = _file.read()
_file.close()
_list = _str.splitlines()

check_list = []
_check = False
for i in _list:
    if not _check:
        if i.strip(":") == _device:
            _check = True
    else:
        if i.startswith(" "):
            check_list.append(i.strip())
        else:
            break

_file = open(bin_dir + "data/panucci.conf")
_str = _file.read()
_file.close()
panucci_conf = _str.splitlines()

_file = open(bin_dir + "data/panucci-all.conf")
_str = _file.read()
_file.close()
panucci_all_conf = _str.splitlines()

for i in range(len(panucci_conf)):
    _option = panucci_conf[i].split("=")[0].strip()
    for j in check_list:
        new_option = j.split("=")[0].strip()
        if new_option == _option:
            panucci_conf[i] = j

for i in range(len(panucci_all_conf)):
    _option = panucci_all_conf[i].split("=")[0].strip()
    for j in check_list:
        new_option = j.split("=")[0].strip()
        if new_option == _option:
            panucci_all_conf[i] = j

_file = open(bin_dir + "data/panucci.conf.new", "w")
for i in panucci_conf:
    _file.write(i + "\n")
_file.close()

_file = open(bin_dir + "data/panucci-all.conf.new", "w")
for i in panucci_all_conf:
    _file.write(i + "\n")
_file.close()
