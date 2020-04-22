#!/usr/bin/env python3

import os
import subprocess

git_bin  = 'git'
java_bin = 'java'

cwd = os.getcwd()

mcdlsnapshot_bin = cwd + '/tools/MinecraftSnapshotServerDownloader/mcdlsnapshot.py'
mcremapper_root  = cwd + '/tools/MC-Remapper'
mcremapper_bin   = mcremapper_root + '/build/install/MC-Remapper/bin/MC-Remapper'
fernflower_root  = cwd + '/tools/fernflower'
fernflower_jar   = fernflower_root + '/build/libs/fernflower.jar'

# initialize git submodules
p = subprocess.run(args=[git_bin, 'submodule', 'update', '--init'])
if p.returncode != 0:
    print('failed to initialize submodules')
    exit(1)

if not os.path.isfile(mcdlsnapshot_bin):
    print('failed to find MinecraftSnapshotServerDownloader')
    exit(1)

if not os.path.isfile(mcremapper_bin):
    # build MC-Remapper
    p = subprocess.run(args=['./gradlew', 'installDist'], cwd=mcremapper_root)
    if p.returncode != 0 or not os.path.isfile(mcremapper_bin):
        print('failed to build MC-Remapper')
        exit(1)
 
if not os.path.isfile(fernflower_jar):
    # build fernflower
    p = subprocess.run(args=['./gradlew', 'jar'], cwd=fernflower_root)
    if p.returncode != 0 or not os.path.isfile(fernflower_jar):
        print('failed to build fernflower')
        exit(1)
