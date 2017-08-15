import os
import time
import paramiko
from wetland import config

# path of log files
logpath = config.cfg.get("log", "path")
if not os.path.exists(logpath):
    os.makedirs(logpath)

paramiko.util.log_to_file(logpath + '/paramiko.log')

# sensor name
name = config.cfg.get("wetland", "name")


class plugin(object):
    def __init__(self, hacker_ip):
        self.hacker_ip = hacker_ip
        self.logpath = None
        self.get_logpath()

    def get_logpath(self):
        self.logpath = os.path.join(logpath, self.hacker_ip)
        if not os.path.exists(self.logpath):
            os.makedirs(self.logpath)

    def send(self, subject, action, content):
        if subject == 'wetland':
            with open(os.path.join(self.logpath, 'wetland.log'), 'a') as logfile:
                log = ' '.join([time.strftime("%y%m%d-%H:%M:%S"),
                               action, content, '\n'])
                logfile.write(log)

        elif subject == 'content':
            with open(os.path.join(self.logpath, action+'.log'), 'a') as logfile:
                log = ' '.join([time.strftime("%y%m%d-%H:%M:%S"),
                                content, '\n'])
                logfile.write(log)

        elif subject in ['sftpfile', 'sftpserver']:
            with open(os.path.join(self.logpath, 'sftp.log'), 'a') as logfile:
                log = ' '.join([time.strftime("%y%m%d-%H:%M:%S"),
                               action, content, '\n'])
                logfile.write(log)
