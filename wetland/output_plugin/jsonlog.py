import json
import datetime
import socket
from wetland import config


class plugin(object):
    def __init__(self, server):
        self.server = server
        self.methods = list(set(['file', 'tcp', 'udp']) &
                            set(config.cfg.options('jsonlog')))
        self.name = config.cfg.get("wetland", "name")

        if 'tcp' in self.methods:
            ip, port = config.cfg.get('jsonlog', 'tcp').split(':')
            port = int(port)
            self.tcpsock = (ip, port)
        if 'udp' in self.methods:
            ip, port = config.cfg.get('jsonlog', 'udp').split(':')
            port = int(port)
            self.udpsock = (ip, port)
        if 'file' in self.methods:
            self.logfile = config.cfg.get('jsonlog', 'file')

    def file(self, data):
        with open(self.logfile, 'a') as logfile:
            logfile.write(data+'\n')

    def udp(self, data):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(self.udpsock)
        s.send(data)
        s.close()

    def tcp(self, data):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.tcpsock)
        s.send(data)
        s.close()

    def send(self, subject, action, content):
        t = datetime.datetime.utcnow().isoformat()

        if subject == 'wetland' and \
           action in ('login_successful', 'shell command', 'exec command',
                      'direct_request', 'reverse_request'):
            pass

        elif subject in ('sftpfile', 'sftpserver'):
            pass

        elif subject == 'content' and action in ('pwd',):
            pass

        elif subject == 'upfile':
            pass

        else:
            return True

        data = {'timestamp': t, 'src_ip': self.server.hacker_ip,
                'dst_ip': self.server.myip, 'action': action,
                'content': content, 'sensor': self.name,
                'src_port': self.server.hacker_port,
                'dst_port': 22}
        data = json.dumps(data) + '\n'
        for m in self.methods:
            getattr(self, m)(data)
        return True
