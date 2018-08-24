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

        self.haslogined = [False]
        self.whitelist = None
        self.blacklist = ['127.0.0.2']
        if self.cfg.getboolean('wetland', 'whitelist') and \
           self.cfg.getboolean('output', 'mqtt'):

            self.whitelist = ['127.0.0.1']
            import json
            import paho.mqtt.client as mqtt

            def on_connect(client, userdata, flags, rc):
                client.subscribe("ck/whitelist")

            def on_message(client, userdata, msg):
                self.whitelist = json.loads(msg.payload)

            host = config.cfg.get("mqtt", "host")
            keys_path = config.cfg.get("mqtt", "keys_path")
            ca_certs = keys_path + 'ca.crt'
            cert_file = keys_path + 'client.crt'
            key_file = keys_path + 'client.key'

            self.mqttclient = mqtt.Client()
            self.mqttclient.on_connect = on_connect
            self.mqttclient.on_message = on_message
            self.mqttclient.tls_set(ca_certs=ca_certs, certfile=cert_file,
                                    keyfile=key_file)
            self.mqttclient.connect(host)
            self.mqttclient.loop_start()
            # thread = threading.Thread(target=lambda x: x.loop_forever(),
            #                          args=(self.mqttclient,))
            # thread.setDaemon(True)
            # thread.start()

        if self.cfg.getboolean("wetland", "req_public_ip"):
            import socket
            import random

            try:
                # TODO: cip.cc is in china
                socket.setdefaulttimeout(20)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.cfg.get('wetland', 'wetland_addr'),
                        random.randint(40000, 60000)))
                s.connect(('www.cip.cc', 80))
                s.send("GET / HTTP/1.1\r\n"
                       "Host:www.cip.cc\r\n"
                       "User-Agent:curl\r\n\r\n")
                self.myip = s.recv(1024).split("\r\n")[-4].split('\n')[0].split(': ')[1]
                s.close()
            except Exception, e:
                print e
                self.myip = None
        else:
            self.myip = None


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

        if self.server.myip:
            myip = self.server.myip
        else:
            myip = transport.sock.getsockname()[0]
        sServer = sshServer.ssh_server(transport=transport, network=nw,
                                       myip=myip,
                                       whitelist=self.server.whitelist,
                                       blacklist=self.server.blacklist,
                                       haslogined=self.server.haslogined)

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
