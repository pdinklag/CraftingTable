#!/usr/bin/env python3

import os
import subprocess

git_bin  = 'git'
java_bin = 'java'

cwd = os.path.dirname(os.path.realpath(__file__))

mcdlsnapshot_bin = os.path.join(cwd, 'tools', 'MinecraftSnapshotServerDownloader', 'mcdlsnapshot.py')
mcremapper_root  = os.path.join(cwd, 'tools', 'MC-Remapper')
mcremapper_bin   = os.path.join(mcremapper_root, 'build', 'install', 'MC-Remapper', 'bin', 'MC-Remapper')
fernflower_root  = os.path.join(cwd, 'tools', 'fernflower')
fernflower_jar   = os.path.join(fernflower_root, 'build', 'libs', 'fernflower.jar')

# initialize git submodules
p = subprocess.run(args=[git_bin, 'submodule', 'update', '--init'], cwd=cwd)
if p.returncode != 0:
    print('failed to initialize submodules')
    exit(1)

if not os.path.isfile(mcremapper_bin):
    # build MC-Remapper
    p = subprocess.run(args=[os.path.join('.', 'gradlew'), 'installDist'], cwd=mcremapper_root)
    if p.returncode != 0 or not os.path.isfile(mcremapper_bin):
        print('failed to build MC-Remapper')
        exit(1)
 
if not os.path.isfile(fernflower_jar):
    # build fernflower
    p = subprocess.run(args=[os.path.join('.', 'gradlew'), 'jar'], cwd=fernflower_root)
    if p.returncode != 0 or not os.path.isfile(fernflower_jar):
        print('failed to build fernflower')
        exit(1)
