import socket
from os.path import join
import paho.mqtt.client as mqtt
import ConfigParser

cfg = ConfigParser.ConfigParser()
cfg.read('wetland.cfg')


class DottableDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

    def allowDotting(self, state=True):
        if state:
            self.__dict__ = self
        else:
            self.__dict__ = dict()


def reqpubip(listen_ip=None):
    outip = None
    inip = None

    while 1:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(20)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if listen_ip:
                s.bind((listen_ip, 0))
            s.connect(('icanhazip.com', 80))
            s.send("GET / HTTP/1.1\r\n"
                   "Host:icanhazip.com\r\n"
                   "User-Agent:curl\r\n\r\n")
            outip = s.recv(1024).split("\r\n")[-1].split('\n')[0]
            inip = s.getsockname()[0]
            return outip, inip
        except Exception, e:
            print 51, e
        finally:
            s.close()


def get_args():
    args = DottableDict()

    # mqtt client
    if cfg.getboolean('output', 'mqtt'):
        # args.keys_path = cfg.get('mqtt', 'keys_path')
        # ca_certs = join(args.keys_path, 'ca.crt')
        # cert_file = join(args.keys_path, 'client.crt')
        # key_file = join(args.keys_path, 'client.key')

        args.mqtthost = cfg.get('mqtt', 'host')
        mqttclient = mqtt.Client()
        # mqttclient.tls_set(ca_certs=ca_certs,
        #                    certfile=cert_file,
        #                    keyfile=key_file)
        mqttclient.username_pw_set(cfg.get('mqtt', 'usr'),
                                   cfg.get('mqtt', 'pwd'))

        mqttclient.connect(args.mqtthost)
        mqttclient.loop_start()

        args.mqttclient = mqttclient

    if cfg.getboolean('wetland', 'req_public_ip'):
        args.myip, args.listen_ip = reqpubip()
    else:
        _, args.myip = reqpubip()
    args.sensor = cfg.get('wetland', 'name')
    args.listen_port = cfg.getint('wetland', 'wetland_port')

    return args


args = get_args()
