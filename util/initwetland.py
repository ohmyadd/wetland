import os
import sys
import shutil

import paramiko
import subprocess

# Get root path
if len(sys.argv) == 1:
    print '[-] please specify wetland\'s root path'
    sys.exit(1)
path = sys.argv[1]
print '[+] Root Path: \t%s' % path

if not os.path.exists(path):
    print '[-] Not Exists: \t root path'
    sys.exit(1)

os.chdir(path)


# Generate keys
print '[+] Checking: \tdata folder'
if os.path.exists('data'):
    print '[+] Exists: \tfolder data'
else:
    print '[+] Creating: \tfolder data'
    os.mkdir('data')

if os.path.exists(os.path.join(path, 'data', 'id_rsa')):
    print '[+] Exists: \tid_rsa'
else:
    print '[+] Creating: \tid_rsa'
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(os.path.join(path, 'data', 'id_rsa'))

if os.path.exists(os.path.join(path, 'data', 'id_dsa')):
    print '[+] Exists: \tid_dsa'
else:
    print '[+] Creating: \tid_dsa'
    key = paramiko.DSSKey.generate(2048)
    key.write_private_key_file(os.path.join(path, 'data', 'id_dsa'))


# Install python dependency
if not os.path.exists('requirements'):
    print '[-] Not found: \trequirements'
    sys.exit(1)

print '[+] Installing:\tpython dependency'
s = subprocess.Popen("pip install -r requirements", shell=True,
                     stdout=subprocess.PIPE)
s.communicate()
if s.returncode:
    print '[-] pip error'
    sys.exit(1)


# Clean root folder
print '[+] Cleaning: \troot folder'

print '[+] Moving: \tdocuments into folder data'
shutil.move('README.md',  'data')
shutil.move('requirements',  'data')

print '[+] Copying: \tcfg.default to cfg'
shutil.copy('wetland.cfg.default', 'wetland.cfg')
shutil.move('wetland.cfg.default',  'data')
