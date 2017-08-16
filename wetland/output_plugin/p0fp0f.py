import os
import p0f
import subprocess
from wetland import config

sock = config.cfg.get("p0fp0f", "sockname")
path = config.cfg.get("p0fp0f", "path")
iface = config.cfg.get("p0fp0f", "iface")
logpath = config.cfg.get("log", "path")

subprocess.Popen("./p0f -d -i %s -s %s" % (iface, sock), shell=True,
                 cwd=path, stdout=subprocess.PIPE)

client = p0f.P0f(os.path.join(path, sock))

class plugin(object):
    def __init__(self, hacker_ip):
        self.hacker_ip = hacker_ip
        self.sent = False

    def send(self, subject, action, content):
        # log one time per transport
        if self.sent:
            return

        with open(os.path.join(logpath, self.hacker_ip, 'p0f.log'), 'a') as lg:
            try:
                lg.write(str(client.get_info(self.hacker_ip)) + '\n')
            except KeyError:
                pass
            else:
                self.sent = True
