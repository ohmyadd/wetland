import os
import sys
import shutil

import paramiko
import subprocess

# Get root path
path = sys.argv[1]
print '[+] root path is %s' % path

if not os.path.exists(path):
    print '[-] root path not exists'
    sys.exit(1)

os.chdir(path)


# Generate keys
print '[+] checking keys'
if os.path.exists('keys'):
    print '[+] keys folder exists'
else:
    print '[+] creating folder keys'
    os.mkdir('keys')

if os.path.exists(os.path.join(path, 'keys', 'id_rsa')):
    print '[+] id_rsa exists'
else:
    print '[+] creating id_rsa'
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(os.path.join(path, 'keys', 'id_rsa'))

if os.path.exists(os.path.join(path, 'keys', 'id_rsa')):
    print '[+] id_rsa exists'
else:
    print '[+] creating id_ds'
    key = paramiko.RSAKey.generate(2048)
    key = paramiko.DSSKey.generate(2048)
    key.write_private_key_file(os.path.join(path, 'keys', 'id_dsa'))


# Install python dependency
if not os.path.exists('requirements'):
    print '[-] requirements not found'
    sys.exit(1)

print '[+] installing python dependency'
s = subprocess.Popen("pip install -r requirements", shell=True,
                     stdout=subprocess.PIPE)
s.communicate()
if s.returncode:
    print '[-] pip error'
    sys.exit(1)


# Clean root folder
print '[+] clean root folder'
os.mkdir('doc')

print '[+] moving documents into folder doc'
shutil.move('README.md',  'doc')
shutil.move('requirements',  'doc')

print '[+] copying cfg.default to cfg'
shutil.copy('wetland.cfg.default', 'wetland.cfg')
shutil.move('wetland.cfg.default',  'doc')
