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
javaFileExt = '.java'
srcPath = os.path.join(dataPath, 'src')
srcPathLen = len(srcPath)
sources = data['sources']

modified = list()
for root, _, files in os.walk(srcPath):
    for name in files:
        if name.endswith(javaFileExt):
            filename = os.path.join(root, name)
            src = filename[srcPathLen+1:]
            if src in sources:
                with open(filename, 'rb') as f:
                    sha1 = hashlib.sha1(f.read()).hexdigest()

                if sha1 != sources[src]:
                    modified.append(filename)
            else:
                modified.append(filename)

if len(modified) == 0:
    print('no source files have been modified!')
    exit(0)

# recompile modified
recompilePath = os.path.join(dataPath, 'recompile')
os.makedirs(recompilePath, exist_ok=True)

# clear all .class files in recompile path
classFileExt = '.class'
for root, _, files in os.walk(recompilePath):
    for name in files:
        if name.endswith(classFileExt):
            os.remove(os.path.join(root, name))

# compile
print('Compiling ' + str(len(modified)) + ' source files ...')
p = subprocess.run(args=['javac','-source','1.8','-target','1.8','-cp',args.remappedServer,'-d',recompilePath] + modified)

if not p.returncode == 0:
    exit(1)

# list recompiled files
pack = set()
for root, _, files in os.walk(recompilePath):
    for name in files:
        if name.endswith(classFileExt):
            pack.add(os.path.join(root, name))

# repack
repackedServer = args.remappedServer[:-3] + 'repack.jar'
print('Repacking into ' + repackedServer + ' ...')

with zipfile.ZipFile(args.remappedServer, 'r') as server:
    with zipfile.ZipFile(repackedServer, 'w') as repack:
        # set comment
        repack.comment = data['jarComment'].encode('utf-8')
        
        # walk files
        for item in server.infolist():
            filename = item.filename
            
            recompiled = os.path.join(recompilePath, filename)
            if os.path.isfile(recompiled):
                pack.remove(recompiled)
                with open(recompiled, 'rb') as f:
                    filedata = f.read()
            else:
                filedata = server.read(filename)

            repack.writestr(item, filedata)
        
        # add remaining class files
        for remaining in pack:
            with open(remaining, 'rb') as f:
                filedata = f.read()

            filename = remaining[len(recompilePath)+1:]
            repack.writestr(filename, filedata)

print('done')
