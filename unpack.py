#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import subprocess

from zipfile import ZipFile
from zipfile import ZIP_DEFLATED

# setup
import setup

# command line arguments
parser = argparse.ArgumentParser(description='CraftingTable Unpacker')
parser.add_argument('server', help='the original server jar')
parser.add_argument('mapping', help='the corresponding obfuscation map')
parser.add_argument('output', help='the output directory')
parser.add_argument('--verbose', action='store_true', help='verbose error messages')
args = parser.parse_args()

# checks
if not os.path.isfile(args.server):
    print('server JAR not found: ' + args.server)

if not os.path.isfile(args.mapping):
    print('obfuscation map not found: ' + args.mapping)

# load previous data
dataFilename = args.output + '/' + args.server[:-3] + 'data.json'

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
remapFilename = args.output + '/' + args.server[:-3] + 'remap.jar'
if serverHash != data['serverHash']:
    print('Remapping ...', flush=True)
    p = subprocess.run(args=[setup.mcremapper_bin, '--autotoken', '--output', remapFilename,  args.server, args.mapping])
    
    if not p.returncode == 0:
        exit(1)
        
    data['serverHash'] = serverHash
    writeData()

# extract classes
javaOutput = args.output + '/src'

def getMainClassFilePath(classfilename):
    dollar = classfilename.find('$')
    if dollar >= 0:
        return classfilename[0:dollar] + '.class'
    else:
        return classfilename

def getSourceFilePath(classfilename):
    return classfilename[:-5] + 'java'

classes = data['classes']
extractClasses = set()

extractPrefix = 'net/minecraft'
extractSuffix = '.class'

classesOutput = args.output + '/classes'

print('extracting ...', flush=True)
# TODO: also check for classes that may have been removed
with ZipFile(remapFilename, 'r') as jar:
    data['jarComment'] = jar.comment.decode('utf-8')

    for item in jar.infolist():
        if item.filename.startswith(extractPrefix) and item.filename.endswith(extractSuffix):
            outfilename = classesOutput + '/' + item.filename
            os.makedirs(os.path.dirname(outfilename), exist_ok=True)
            
            classdata = jar.read(item.filename)
            sha1 = hashlib.sha1(classdata).hexdigest()
            
            mainClass = getMainClassFilePath(item.filename)
            srcFile = javaOutput + '/' + getSourceFilePath(mainClass)
            if not item.filename in classes or sha1 != classes[item.filename] or not os.path.isfile(srcFile):
                classes[item.filename] = sha1
                extractClasses.add(mainClass)
            
                with open(outfilename, 'wb') as f:
                    f.write(classdata)

if len(extractClasses) > 0:
    print('extracted ' + str(len(extractClasses)) + ' classes')
else:
    print('no classes to extract, everything already up to date!')
    writeData()
    exit(0)

# decompile
sources = data['sources']
srcPrefixLength = len(javaOutput) + 1

print('decompiling ...', flush=True)
totalStr = str(len(extractClasses))
num = 0

for filename in extractClasses:
    num += 1

    basename = os.path.basename(filename)
    if basename.find('$') >= 0:
        # skip inner classes
        continue

    classfilename = classesOutput + '/' + filename
    srcfilename = javaOutput + '/' + getSourceFilePath(filename)
    srcdir = os.path.dirname(srcfilename)
    os.makedirs(srcdir, exist_ok=True)
    
    # build a filename pattern that will include all potential inner classes of the class
    classpattern = classfilename[:-6] + '*.class' # replace .class by *.class
    cmdline = 'java -jar ' + setup.fernflower_jar + ' -dgs=1 -rsy=1 ' + classpattern + ' ' + srcdir
    p = subprocess.run(args=[cmdline], shell=True, capture_output=(not args.verbose))
    
    if p.returncode == 0 and os.path.isfile(srcfilename):
        with open(srcfilename, 'rb') as f:
            sha1 = hashlib.sha1(f.read()).hexdigest()

        sources[srcfilename[srcPrefixLength:]] = sha1
        print('\t(' + str(num) + '/' + totalStr + ') ' + srcfilename, flush=True)
    else:
        print('\t(' + str(num) + '/' + totalStr + ') ' + srcfilename + ' [FAILED]', flush=True)

# write data
writeData()

# done
print('done')
