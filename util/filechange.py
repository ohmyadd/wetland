import os
import sys
import shutil

if len(sys.argv) == 1:
    print '[-] input container\'s id'
    sys.exit(1)

ID = sys.argv[1]
if ID == '-':
    ID = sys.stdin.read().strip()
if len(ID) != 64:
    print '[-] length of ID must be 64'
    sys.exit(1)

layer_id_file = '/var/lib/docker/image/aufs/layerdb/mounts/%s/mount-id' % ID
if not os.path.exists(layer_id_file):
    print '[-] container not exists'

with open(layer_id_file) as f:
    layer_id = f.read()
print '[+] read-write layer ID: %s' % layer_id

shutil.copytree('/var/lib/docker/aufs/diff/%s' % layer_id, layer_id)
print '[+] copy to ./%s' % layer_id
