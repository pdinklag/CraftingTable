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
parser.add_argument('output', help='the output directory')
args = parser.parse_args()

# constants
jarCommentFilename = args.output + '/jar_comment'
hashesFilename = args.output + '/class_hashes'

classesOutput = args.output + '/classes'
javaOutput = args.output + '/src'

extractPrefix = 'net/minecraft'
extractSuffix = '.class'

# download latest snapshot
print('Checking for latest snapshot ...', flush=True)
p = subprocess.run(args=[setup.mcdlsnapshot_bin, '-s', '-m', '--print-always'], capture_output=True, cwd=args.output)

if not p.returncode == 0:
    print(p.stderr.decode())
    exit(1)

serverJar = args.output + '/' + p.stdout.decode().strip()
serverMapping = serverJar[:-3] + 'mapping.txt'

# remap
print('Remapping ...', flush=True)
serverRemapJar = serverJar[:-3] + 'remap.jar'

if not os.path.isfile(serverRemapJar):
    p = subprocess.run(args=[setup.mcremapper_bin, '--input', serverJar, '--mapping', 'file://' + os.path.abspath(serverMapping), '--output', serverRemapJar])
    
    if not p.returncode == 0:
        exit(1)

# load previous hashes
if os.path.isfile(hashesFilename):
    with open(hashesFilename, 'r') as f:
        classes = json.load(f);
else:
    classes = dict()

changedClasses = []

print('processing server JAR ...', flush=True)
with ZipFile(serverRemapJar, 'r') as jar:
    with open(jarCommentFilename, 'wb') as f:
        f.write(jar.comment)

    for item in jar.infolist():
        if item.filename.startswith(extractPrefix) and item.filename.endswith(extractSuffix):
            outfilename = classesOutput + '/' + item.filename
            os.makedirs(os.path.dirname(outfilename), exist_ok=True)
            
            classdata = jar.read(item.filename)
            sha1 = hashlib.sha1(classdata).hexdigest()
            
            if not item.filename in classes or sha1 != classes[item.filename]:
                classes[item.filename] = sha1
                changedClasses.append(item.filename)
            
                with open(outfilename, 'wb') as f:
                    f.write(classdata)

if len(changedClasses) == 0:
    print('nothing has changed!')
    exit(0)

# decompile
print('decompiling ...', flush=True)
totalStr = str(len(changedClasses))
num = 0

for filename in changedClasses:
    num += 1

    basename = os.path.basename(filename)
    if basename.find('$') >= 0:
        # skip inner classes
        continue

    classfilename = classesOutput + '/' + filename
    srcdir = os.path.dirname(javaOutput + '/' + filename)
    os.makedirs(srcdir, exist_ok=True)
    
    # build a filename pattern that will include all potential inner classes of the class
    classpattern = classfilename[:-6] + '*.class' # replace .class by *.class
    cmdline = 'java -jar ' + setup.fernflower_jar + ' -rsy=1 ' + classpattern + ' ' + srcdir
    p = subprocess.run(args=[cmdline], shell=True, capture_output=True)
    
    if p.returncode == 0:
        print('\t(' + str(num) + '/' + totalStr + ') ' + classfilename, flush=True)
    else:
        print('\t(' + str(num) + '/' + totalStr + ') ' + classfilename + ' [FAILED]', flush=True)

# write class hashes
print('writing hashes ...', flush=True)
with open(hashesFilename, 'w') as f:
    json.dump(classes, f)
