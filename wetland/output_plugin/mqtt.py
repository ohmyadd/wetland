import json
import datetime
from wetland.config import args


class plugin(object):
    def __init__(self, server):
        self.server = server

    def send(self, subject, action, content):
        t = datetime.datetime.utcnow().isoformat()

        if subject == 'wetland' and \
           action in ('login_successful', 'shell command', 'exec command',
                      'direct_request', 'reverse_request', 'download'):
            pass

        elif subject in ('sftpfile', 'sftpserver'):
            pass

        elif subject == 'content' and action in ('pwd',):
            pass

        elif subject == 'upfile':
            pass

        # do not log to server
        else:
            return True

        data = {'timestamp': t, 'src_ip': self.server.hacker_ip,
                'dst_ip': args.myip, 'action': action,
                'content': content, 'sensor': args.sensor,
                'src_port': self.server.hacker_port,
                'dst_port': args.listenport, 'honeypot': 'wetland',
                'session': self.server.sessionuid}
        data = json.dumps(data)
        args.mqttclient.publish('ck/log/wetland', data, qos=1)
        return True
