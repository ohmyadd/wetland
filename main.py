from wetland import config
from wetland.server import tcpServer

import paramiko
paramiko.util.log_to_file('./paramiko.log')

address = config.cfg.get("wetland", "wetland_addr")
port = config.cfg.getint("wetland", "wetland_port")


if __name__ == '__main__':
    tServer = tcpServer.tcp_server((address, port), tcpServer.tcp_handler)
    tServer.serve_forever()
