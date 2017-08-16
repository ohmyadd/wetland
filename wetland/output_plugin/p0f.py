import os
import p0f
import json
import subprocess
from wetland import config

sock = config.cfg.get("p0f", "sockname")
path = config.cfg.get("p0f", "path")
logpath = config.cfg.get("log", "path")

subprocess.Popen("./p0f -d -s {sock}", shell=True, cwd=path, stdout=None)

client = p0f.P0f(os.path.join(path, sock))

class plugin(object):
    def __init__(self, hacker_ip):
        self.hacker_ip = hacker_ip

    def send(self, subject, action, content):
        with open(os.join(logpath, hacker_ip, 'p0f.log'), 'a') as log:
            log.write(json.dumps(client.get_info(self.hacker_ip)) + '\n')
