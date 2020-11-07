#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import subprocess
import zipfile

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
# TODO: first clear all class files in recompile path!
recompilePath = dataPath + '/recompile'
os.makedirs(recompilePath, exist_ok=True)

print('Compiling ' + str(len(modified)) + ' source files ...')
p = subprocess.run(args=['javac','-source','1.8','-target','1.8','-cp',args.remappedServer,'-d',recompilePath] + modified)

if not p.returncode == 0:
    exit(1)

# repack
# TODO: also pack new files that are not contained in the original server
repackedServer = args.remappedServer[:-3] + 'repack.jar'
print('Repacking into ' + repackedServer + ' ...')

with zipfile.ZipFile(args.remappedServer, 'r') as server:
    with zipfile.ZipFile(repackedServer, 'w') as repack:
        # set comment
        repack.comment = data['jarComment'].encode('utf-8')
        
        # walk files
        for item in server.infolist():
            filename = item.filename
            
            recompiled = recompilePath + '/' + filename
            if os.path.isfile(recompiled):
                with open(recompiled, 'rb') as f:
                    filedata = f.read()
            else:
                filedata = server.read(filename)

            repack.writestr(item, filedata)

print('done')
