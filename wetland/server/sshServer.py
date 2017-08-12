#!/usr/bin/env python
import socket
import threading
import traceback

from wetland import geoip
from wetland import services
from wetland import output_plugins as output
from wetland import config
from wetland.log import loggers

import paramiko
from paramiko.py3compat import b, u, decodebytes


class ssh_server(paramiko.ServerInterface):

    def __init__(self, transport, network):
        self.cfg = config.cfg

        self.hacker_trans = transport
        self.docker_host = self.cfg.get("wetland", "docker_addr")
        self.docker_port = self.cfg.getint("wetland", "docker_port")
        self.docker_trans = None

        self.hacker_ip, self.hacker_port = transport.getpeername()
        self.geoinfo = geoip.geoip.record_by_addr(self.hacker_ip)

        self.network = network

        self.loggers = loggers()
        self.wd_logger = self.loggers.get2('wetland')
        self.pwd_logger = self.loggers.get('pwd', self.hacker_ip)
        self.shell_logger = self.loggers.get('shell', self.hacker_ip)
        self.exec_logger = self.loggers.get('exec', self.hacker_ip)
        self.direct_logger = self.loggers.get('direct', self.hacker_ip)
        self.reverse_logger = self.loggers.get('reverse', self.hacker_ip)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((str(self.network.fake_ip), self.hacker_port))
        self.sock.connect((self.docker_host, self.docker_port))

        self.docker_trans = paramiko.Transport(self.sock)
        self.docker_trans.start_client()


    # check auth
    def get_allowed_auths(self, username):
        return 'password'

    def check_auth_password(self, username, password):
        self.pwd_logger.info(':::'.join((username, password)))
        output.output(level='info', Hacker_IP=self.hacker_ip,
                      Login_As=username, Action='Brute Password',
                      Password=password)

        try:
            self.docker_trans.auth_password(username=username,
                                            password=password)
        except Exception, e:
            return paramiko.AUTH_FAILED

        else:
            # self.docker_trans = docker_trans

            self.wd_logger.info("%s:%d login successful as %s"%(self.hacker_ip,
                                                 self.hacker_port, username))

            output.output(level='warning', Hacker_IP=self.hacker_ip,
                          Login_As=username, Action='Login Success',
                          Country=self.geoinfo['country_name'],
                          City=self.geoinfo['city'])

            return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        # if (username == 'robey') and (key == self.good_pub_key):
        return paramiko.AUTH_FAILED

    # check kinds of requests
    def check_channel_request(self, kind, chanid):
        self.wd_logger.info("%s:%d channel request kind: %s channel"%(
                                       self.hacker_ip, self.hacker_port, kind))
        return paramiko.OPEN_SUCCEEDED

    def check_global_request(self, kind, msg):
        self.wd_logger.info("%s:%d global request kind: %s"%(self.hacker_ip,
                                             self.hacker_port, kind))
        return True

    def check_channel_pty_request(self, channel, term, width, height,
                                  pixelwidth, pixelheight, modes):
        self.wd_logger.info("%s:%d pty request"%(self.hacker_ip,
                                                 self.hacker_port))
        return True

    def check_channel_shell_request(self, hacker_session):

        try:
            self.wd_logger.info("%s:%d shell request"%(self.hacker_ip,
                                                     self.hacker_port))
            docker_session = self.docker_trans.open_session()
            docker_session.get_pty()
            docker_session.invoke_shell()

            service_thread = threading.Thread(target=services.shell_service,
                                      args=(hacker_session, docker_session,
                                      self.shell_logger, self.wd_logger))
            service_thread.setDaemon(True)
            service_thread.start()

        except Exception as e:
            self.wd_logger.debug("%s:%d shell request error %s" %(
                                        self.hacker_ip, self.hacker_port, e))
            return False
        else:
            return True

    def check_channel_exec_request(self, hacker_session, command):

        try:
            self.wd_logger.info("%s:%d exec request"%(self.hacker_ip,
                                                     self.hacker_port))
            docker_session = self.docker_trans.open_session()
            service_thread = threading.Thread(target=services.exec_service,
                            args=(hacker_session, docker_session, command,
                                  self.exec_logger, self.wd_logger))
            service_thread.setDaemon(True)
            service_thread.start()
        except Exception as e:
            self.wd_logger.debug("exec request error:%s" % e)
            return False
        else:
            return True

    def check_port_forward_request(self, address, port):
        self.wd_logger.info("%s:%d port forward request"%(self.hacker_ip,
                                                          self.hacker_port))

        def handler(chann, ori, dest):
            services.reverse_handler(chann, ori, dest, self.hacker_trans,
                                     self.reverse_logger, self.wd_logger)

        flag = self.docker_trans.request_port_forward(address, port,
                                                   handler=handler)
        return flag

    def check_channel_forward_agent_request(self, channel):
        self.wd_logger.info("%s:%d forward agent request"%(self.hacker_ip,
                                                          self.hacker_port))
        return False

    def check_channel_env_request(self, channel, name, value):
        self.wd_logger.info("%s:%d env set request: %s:%s"%(self.hacker_ip,
                                               self.hacker_port, name, value))
        channel.set_environment_variable(name, value)
        return True

    def check_channel_direct_tcpip_request(self, chanid, origin, destination):

        self.wd_logger.info("%s:%s direct tcpip request origin:%s dest:%s" % (
                       self.hacker_ip, self.hacker_port, origin, destination))
        try:
            docker_channel = self.docker_trans.open_channel('direct-tcpip',
                                                     dest_addr=destination,
                                                     src_addr=origin)
        except paramiko.ChannelException as e:
            self.wd_logger.debug("direct request error:%s" % e)
            return paramiko.OPEN_FAILED_CONNECT_FAILED

        service_thread = threading.Thread(target=services.direct_service,
                                          args=(chanid, self.hacker_trans,
                                                docker_channel,
                                                self.direct_logger,
                                                self.wd_logger))
        service_thread.setDaemon(True)
        service_thread.start()
        return paramiko.OPEN_SUCCEEDED
