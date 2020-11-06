#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import subprocess

# command line arguments
parser = argparse.ArgumentParser(description='CraftingTable Packer')
parser.add_argument('remappedServer', help='the (remapped) server JAR')
parser.add_argument('data', help='the data file')
args = parser.parse_args()

if not os.path.isfile(args.remappedServer):
    print('remapped server JAR does not exist: ' + args.remappedServer)
    exit(1)

if not os.path.isfile(args.data):
    print('data file does not exist: ' + args.data)
    exit(1)

# load data
dataPath = os.path.abspath(os.path.dirname(args.data))
with open(args.data, 'r') as f:
    data = json.load(f)

# check source files for modifications
srcPath = dataPath + '/src'

modified = []
for src, srcHash in data['sources'].items():
    filename = srcPath + '/' + src
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()

        if sha1 != srcHash:
            modified.append(filename)
    else:
        print('source file ' + filename + ' does not exist')

if len(modified) == 0:
    print('no source files have been modified!')
    exit(0)

# recompile modified
recompilePath = dataPath + '/recompile'
os.makedirs(recompilePath, exist_ok=True)

print('Compiling ' + str(modified) + ' ...')
p = subprocess.run(args=['javac','-source','1.8','-target','1.8','-cp',args.remappedServer,'-d',recompilePath] + modified)
