#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import subprocess
import zipfile

# setup
import setup

# command line arguments
parser = argparse.ArgumentParser(description='CraftingTable Unpacker')
parser.add_argument('server', help='the original server jar')
parser.add_argument('mapping', help='the corresponding obfuscation map')
parser.add_argument('output', help='the output directory')
parser.add_argument('--verbose', action='store_true', help='verbose error messages')
parser.add_argument('--force-remap', action='store_true', help='force remapping')
parser.add_argument('--force-decompile', action='store_true', help='force decompilation')
parser.add_argument('--force-rehash', action='store_true', help='force re-hashing of source files')
args = parser.parse_args()

# checks
if not os.path.isfile(args.server):
    print('server JAR not found: ' + args.server)

if not os.path.isfile(args.mapping):
    print('obfuscation map not found: ' + args.mapping)

# load previous data
dataFilename = os.path.join(args.output, args.server[:-3] + 'data.json')

if os.path.isfile(dataFilename):
    with open(dataFilename, 'r') as f:
        data = json.load(f)
else:
    data = dict()
    data['classes'] = dict()
    data['sources'] = dict()
    data['serverHash'] = ''
    data['jarComment'] = ''

# write data function
def writeData():
    global data, dataFilename
    
    print('writing data to ' + dataFilename + ' ...', flush=True)
    with open(dataFilename, 'w') as f:
        json.dump(data, f)

# compute server hash
with open(args.server, 'rb') as f:
    serverHash = hashlib.sha1(f.read()).hexdigest()

# remap
remapFilename = os.path.join(args.output, args.server[:-3] + 'remap.jar')
if args.force_remap or serverHash != data['serverHash']:
    print('Remapping ...', flush=True)
    p = subprocess.run(args=[setup.mcremapper_bin, '--autotoken', '--output-name', remapFilename,  args.server, args.mapping])
    
    if not p.returncode == 0:
        exit(1)
        
    data['serverHash'] = serverHash
    writeData()

# extract classes
javaOutput = os.path.join(args.output, 'src')
classesOutput = os.path.join(args.output, 'classes')

classes = data['classes']

classFileExt = '.class'
javaFileExt = '.java'

print('extracting ...', flush=True)
numChanged = 0

# TODO: also check for classes that may have been removed
with zipfile.ZipFile(remapFilename, 'r') as jar:
    data['jarComment'] = jar.comment.decode('utf-8')

    for item in jar.infolist():
        filename = item.filename
        if filename.endswith(classFileExt) and (filename.startswith('net/minecraft') or filename.startswith('com/mojang')):
            outfilename = os.path.join(classesOutput, filename)
            os.makedirs(os.path.dirname(outfilename), exist_ok=True)
            
            classdata = jar.read(filename)
            sha1 = hashlib.sha1(classdata).hexdigest()
            
            if not filename in classes or sha1 != classes[filename]:
                numChanged += 1
                classes[filename] = sha1
            
                with open(outfilename, 'wb') as f:
                    f.write(classdata)

if args.force_decompile or numChanged > 0:
    print(str(numChanged) + ' classes have changed')

    # clear all .java files in source path
    for root, _, files in os.walk(javaOutput):
        for name in files:
            if name.endswith(javaFileExt):
                os.remove(os.path.join(root, name))

    # decompile
    print('decompiling ...', flush=True)
    os.makedirs(javaOutput, exist_ok=True)
    p = subprocess.run(args=['java', '-jar', setup.fernflower_jar, '-dgs=1', '-rsy=1', '-ind=    ', classesOutput, javaOutput], capture_output=not args.verbose)
    
else:
    print('everything up to date!')

# compute source file hashes
if args.force_decompile or args.force_rehash or numChanged > 0:
    data['sources'] = dict()
    sources = data['sources']
    javaPrefixLength = len(javaOutput) + 1

    for root, _, files in os.walk(javaOutput):
        for name in files:
            if name.endswith(javaFileExt):
                srcfilename = os.path.join(root, name)
                with open(srcfilename, 'rb') as f:
                    srchash = hashlib.sha1(f.read()).hexdigest()
                
                sources[srcfilename[javaPrefixLength:]] = srchash

# write data
writeData()

# done
print('done')
