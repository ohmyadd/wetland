import json
import uuid
import paramiko
from collections import defaultdict

from wetland.services import SocketServer
from wetland.server import sshServer
from wetland.server import sftpServer
from wetland.config import cfg, args


class tcp_server(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, sock, handler):
        super(tcp_server, self).__init__(sock, handler)
        self.cfg = cfg

        self.whitelist = None
        self.blacklist = defaultdict(lambda: 0)
        self.sessions = {}

        if self.cfg.getboolean('wetland', 'whitelist') and \
           self.cfg.getboolean('output', 'mqtt'):

            self.whitelist = ['127.0.0.1']

            def on_connect(client, userdata, flags, rc):
                client.subscribe("ck/ctr/wetland/whitelist")

            def on_message(client, userdata, msg):
                newwhitelist = json.loads(msg.payload)
                # runtime update the whitelist in sshserver
                for _ in range(len(self.whitelist)):
                    del self.whitelist[0]
                for i in newwhitelist:
                    self.whitelist.append(i)
                print 'whitelist', self.whitelist

            args.mqttclient.subscribe("ck/ctr/wetland/whitelist")
            args.mqttclient.on_connect = on_connect
            args.mqttclient.on_message = on_message


class tcp_handler(SocketServer.BaseRequestHandler):
    def handle(self):
        transport = paramiko.Transport(self.request)

        rsafile = self.server.cfg.get("ssh", "private_rsa")
        dsafile = self.server.cfg.get("ssh", "private_dsa")
        rsakey = paramiko.RSAKey(filename=rsafile)
        dsakey = paramiko.DSSKey(filename=dsafile)
        transport.add_server_key(rsakey)
        transport.add_server_key(dsakey)

        transport.local_version = self.server.cfg.get("ssh", "banner")

        transport.set_subsystem_handler('sftp', paramiko.SFTPServer,
                                        sftpServer.sftp_server)

        hacker_addr = transport.getpeername()[0]
        if hacker_addr not in self.server.sessions:
            uid = uuid.uuid4().get_hex()
            self.server.sessions[hacker_addr] = uid
        else:
            uid = self.server.sessions[hacker_addr]
        sServer = sshServer.ssh_server(transport=transport,
                                       whitelist=self.server.whitelist,
                                       blacklist=self.server.blacklist,
                                       sessionuid=uid)

        try:
            transport.start_server(server=sServer)
        except paramiko.SSHException:
            return
        except Exception as e:
            print e
            sServer.docker_trans.close()
            return

        try:
            while True:
                chann = transport.accept(60)
                # no channel left
                if not transport._channels.values():
                    break
        except Exception as e:
            print e
        finally:
            sServer.docker_trans.close()
