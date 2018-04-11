#!/usr/bin/env python
import socket
import threading

import paramiko

from wetland import config
from wetland import services
from wetland.output import output


class ssh_server(paramiko.ServerInterface):

    def __init__(self, transport, network, myip):
        self.cfg = config.cfg
        self.network = network
        self.myip = myip

        # init hacker's transport
        self.hacker_trans = transport
        self.hacker_ip, self.hacker_port = transport.getpeername()

        self.opt = output(self)

        self.docker_host = self.cfg.get("wetland", "docker_addr")
        self.docker_port = self.cfg.getint("wetland", "docker_port")

        # bind docker' socket on fake ip
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.cfg.get("network", "enable").lower() == 'true':
            sock.bind((str(self.network.fake_ip), self.hacker_port))
        sock.connect((self.docker_host, self.docker_port))

        # init docker's transport with socket
        self.docker_trans = paramiko.Transport(sock)
        self.docker_trans.start_client()

        # {hacker channel : docker channel}
        self.chain = {}

    # check auth
    def get_allowed_auths(self, username):
        return 'password'

    def check_auth_password(self, username, password):

        self.opt.o('content', 'pwd', ":".join((username, password)))
        try:
            # redirect all auth request to sshd container
            self.docker_trans.auth_password(username=username,
                                            password=password)
        except Exception:
            return paramiko.AUTH_FAILED
        else:
            self.opt.o('wetland', 'login', 'login successful')
            return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED

    # check the kind of channel can be opened
    def check_channel_request(self, kind, chanid):
        self.opt.o('wetland', 'channel_request', kind)
        return paramiko.OPEN_SUCCEEDED

    def check_global_request(self, kind, msg):
        self.opt.o('wetland', 'global_request', str(msg))
        return True

    def check_channel_pty_request(self, channel, term, width, height,
                                  pixelwidth, pixelheight, modes):
        try:
            docker_session = self.docker_trans.open_session()
            docker_session.get_pty()
            self.chain[channel.get_id()] = docker_session.get_id()
        except Exception:
            self.opt.o('wetland', 'pty_request', "failed")
            return False
        else:
            self.opt.o('wetland', 'pty_request', "success")
            return True

    def check_channel_shell_request(self, hacker_session):
        try:
            docker_id = self.chain[hacker_session.get_id()]
            docker_session = self.docker_trans._channels.get(docker_id)
        except Exception:
            docker_session = self.docker_trans.open_session()
            docker_session.get_pty()
            self.chain[hacker_session.get_id()] = docker_session.get_id()

        try:
            docker_session.invoke_shell()

            service_thread = threading.Thread(target=services.shell_service,
                                              args=(hacker_session,
                                                    docker_session,
                                                    self.opt))
            service_thread.setDaemon(True)
            service_thread.start()

        except Exception:
            self.opt.o('wetland', 'shell_request', "failed")
            return False
        else:
            self.opt.o('wetland', 'shell_request', "success")
            return True

    def check_channel_exec_request(self, hacker_session, command):

        try:
            docker_session = self.docker_trans.open_session()
            self.chain[hacker_session.get_id()] = docker_session.get_id()
            service_thread = threading.Thread(target=services.exec_service,
                                              args=(hacker_session,
                                                    docker_session,
                                                    command,
                                                    self.opt))
            service_thread.setDaemon(True)
            service_thread.start()
        except Exception:
            self.opt.o('wetland', 'exec_request', "failed")
            return False
        else:
            self.opt.o('wetland', 'exec_request', "success")
            return True

    # check for reverse forward channel
    def check_port_forward_request(self, address, port):
        def handler(chann, ori, dest):
            services.reverse_handler(chann, ori, dest, self.hacker_trans,
                                     self.opt)

        flag = self.docker_trans.request_port_forward(address, port,
                                                      handler=handler)
        tmp = "success" if flag else 'failed'
        self.opt.o('wetland', 'reverse_request',
                   ', '.join([tmp, address, str(port)]))

        return flag

    def check_channel_forward_agent_request(self, channel):
        self.opt.o('wetland', 'agent_request', 'failed')
        return False

    def check_channel_env_request(self, channel, name, value):
        try:
            docker_id = self.chain[channel.get_id()]
            docker_session = self.docker_trans._channels.get(docker_id)
            docker_session.set_environment_variable(name, value)
        except Exception:
            self.opt.o('wetland', 'env_request', 'failed')
            return False
        else:
            self.opt.o('wetland', 'env_request', 'success')
            return True

    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        try:
            docker_channel = self.docker_trans.open_channel('direct-tcpip',
                                                     dest_addr=destination,
                                                     src_addr=origin)
            self.chain[chanid] = docker_channel.get_id()

        except paramiko.ChannelException:
            self.opt.o('wetland', 'direct_request', 'failed')
            return paramiko.OPEN_FAILED_CONNECT_FAILED
        else:
            self.opt.o('wetland', 'direct_request',
                       'ori:%s, dest:%s' % (origin, destination))
            service_thread = threading.Thread(target=services.direct_service,
                                              args=(chanid,
                                                    self.hacker_trans,
                                                    docker_channel,
                                                    self.opt))
            service_thread.setDaemon(True)
            service_thread.start()
            return paramiko.OPEN_SUCCEEDED
