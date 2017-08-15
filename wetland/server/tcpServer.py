import paramiko

from wetland.services import SocketServer
from wetland.server import sshServer
from wetland.server import sftpServer
from wetland import network
from wetland import config


class tcp_server(SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, sock, handler):
        super(tcp_server, self).__init__(sock, handler)
        self.cfg = config.cfg


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
        nw = network.network(self.client_address[0],
                    self.server.cfg.get("wetland", "docker_addr"))
        nw.create()

        sServer = sshServer.ssh_server(transport=transport, network=nw)

        try:
            transport.start_server(server=sServer)
        except paramiko.SSHException:
            return
        except Exception as e:
            print e
            nw.delete()
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
            nw.delete()
            sServer.docker_trans.close()
