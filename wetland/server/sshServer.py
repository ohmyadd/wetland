#!/usr/bin/env python
import socket
import threading
import traceback

from wetland import config
from wetland import services
from wetland import output as opt

import paramiko


class ssh_server(paramiko.ServerInterface):

    def __init__(self, transport, network):
        self.cfg = config.cfg
        self.network = network

        # init hacker's transport
        self.hacker_trans = transport
        self.hacker_ip, self.hacker_port = transport.getpeername()

        self.docker_host = self.cfg.get("wetland", "docker_addr")
        self.docker_port = self.cfg.getint("wetland", "docker_port")

        # bind docker' socket on fake ip
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

        opt.output('pwd', self.hacker_ip, 'auth', ":".join((username,
                                                            password)))
        try:
            # redirect all auth request to sshd container
            self.docker_trans.auth_password(username=username,
                                            password=password)
        except Exception, e:
            return paramiko.AUTH_FAILED
        else:
            opt.output('wetland', self.hacker_ip, 'login', 'login successful')
            return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED

    # check the kind of channel can be opened
    def check_channel_request(self, kind, chanid):
        opt.output('wetland', self.hacker_ip, 'channel_request', kind)
        return paramiko.OPEN_SUCCEEDED

    def check_global_request(self, kind, msg):
        opt.output('wetland', self.hacker_ip, 'global_request', kind+msg)
        return True

    def check_channel_pty_request(self, channel, term, width, height,
                                  pixelwidth, pixelheight, modes):
        try:
            docker_session = self.docker_trans.open_session()
            docker_session.get_pty()
            self.chain[channel.get_id()] = docker_session.get_id()
        except Exception as e:
            opt.output('wetland', self.hacker_ip, 'pty_request', "failed")
            return False
        else:
            opt.output('wetland', self.hacker_ip, 'pty_request', "success")
            return True

    def check_channel_shell_request(self, hacker_session):
        try:
            docker_id = self.chain[hacker_session.get_id()]
            docker_session = self.docker_trans._channels.get(docker_id)
        except Exception as e:
            docker_session = self.docker_trans.open_session()
            docker_session.get_pty()
            self.chain[channel.get_id()] = docker_session.get_id()

        try:
            docker_session.invoke_shell()

            service_thread = threading.Thread(target=services.shell_service,
                                      args=(hacker_session, docker_session))
            service_thread.setDaemon(True)
            service_thread.start()

        except Exception as e:
            opt.output('wetland', self.hacker_ip, 'shell_request', "failed")
            return False
        else:
            opt.output('wetland', self.hacker_ip, 'shell_request', "success")
            return True

    def check_channel_exec_request(self, hacker_session, command):

        try:
            docker_session = self.docker_trans.open_session()
            self.chain[hacker_session.get_id()] = docker_session.get_id()
            service_thread = threading.Thread(target=services.exec_service,
                                              args=(hacker_session,
                                                    docker_session,
                                                    command))
            service_thread.setDaemon(True)
            service_thread.start()
        except Exception as e:
            opt.output('wetland', self.hacker_ip, 'exec_request', "failed")
            return False
        else:
            opt.output('wetland', self.hacker_ip, 'exec_request', "success")
            return True

    # check for reverse forward channel
    def check_port_forward_request(self, address, port):
        def handler(chann, ori, dest):
            services.reverse_handler(chann, ori, dest, self.hacker_trans)

        flag = self.docker_trans.request_port_forward(address, port,
                                                      handler=handler)
        tmp = "success" if flag else 'failed'
        opt.output('wetland', self.hacker_ip, 'reverse_request', tmp)

        return flag

    def check_channel_forward_agent_request(self, channel):
        opt.output('wetland', self.hacker_ip, 'agent_request', 'failed')
        return False

    def check_channel_env_request(self, channel, name, value):
        try:
            docker_id = self.chain[hacker_session.get_id()]
            docker_session = self.docker_trans._channels.get(docker_id)
            docker_session.set_environment_variable(name, value)
        except Exception as e:
            opt.output('wetland', self.hacker_ip, 'env_request', 'failed')
            return False
        else:
            opt.output('wetland', self.hacker_ip, 'env_request', 'success')
            return True

    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        try:
            docker_channel = self.docker_trans.open_channel('direct-tcpip',
                                                     dest_addr=destination,
                                                     src_addr=origin)
            self.chain[hacker_session.get_id()] = docker_session.get_id()

        except paramiko.ChannelException as e:
            opt.output('wetland', self.hacker_ip, 'direct_request', 'failed')
            return paramiko.OPEN_FAILED_CONNECT_FAILED
        else:
            opt.output('wetland', self.hacker_ip, 'direct_request', 'success')
            service_thread = threading.Thread(target=services.direct_service,
                                              args=(chanid,
                                                    self.hacker_trans,
                                                    docker_channel,
                                                    self.direct_logger,
                                                    self.wd_logger))
            service_thread.setDaemon(True)
            service_thread.start()
            return paramiko.OPEN_SUCCEEDED
