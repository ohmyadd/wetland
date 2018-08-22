import os
import hashlib
import requests
import threading
import subprocess
from wetland.config import cfg
from importlib import import_module as impt

import paho.mqtt.client as mqtt


def get_plugins():
    pname = []
    for k, v in cfg.items('output'):
        if v == 'true':
            pname.append(k)
    return pname


pname = get_plugins()


def download(script):
    s = subprocess.Popen('docker run --rm -e SPSTR="" -e STSTR="" '
                         'ohmyadd/parsewget -c "%s"' % script,
                         shell=True, stdout=subprocess.PIPE)
    result = [i for i in s.stdout.read().split('\n') if i]
    for url in result:
        if '://' not in url:
            url = 'http://' + url

        print url
        try:
            binary = requests.get(url).content
        except Exception, e:
            print e
            continue
        filename = hashlib.sha256(binary).hexdigest()
        upload(filename, binary)


def upload(filename, content=None):
    host = cfg.get("mqtt", "host")
    keys_path = cfg.get("mqtt", "keys_path")
    ca_certs = keys_path + 'ca.crt'
    cert_file = keys_path + 'client.crt'
    key_file = keys_path + 'client.key'

    file_path = os.path.join(cfg.get('files', 'path'), filename)
    if not content:
        with open(file_path, 'rb') as bin:
            content = bin.read()
            filename = hashlib.sha256(content).hexdigest()

    client = mqtt.Client()
    client.tls_set(ca_certs=ca_certs,
                   certfile=cert_file,
                   keyfile=key_file)
    client.connect(host)
    client.publish('ck/file/' + filename, content.encode('base64'), qos=1)


class output(object):
    def __init__(self, server):
        self.server = server
        self.plugins = [impt('wetland.output_plugin.'+n).plugin(self.server)
                        for n in pname]

    def o(self, *args):
        for p in self.plugins:
            thread = threading.Thread(target=p.send, args=args)
            thread.setDaemon(True)
            thread.start()

    def upfile(self, filename):
        if cfg.getboolean('output', 'mqtt') and cfg.getboolean('mqtt', 'upfiles'):
            thread = threading.Thread(target=upload, args=(filename,))
            thread.setDaemon(True)
            thread.start()

    def downandup(self, script):
        if cfg.getboolean('output', 'mqtt') and cfg.getboolean('mqtt', 'upfiles'):
            thread = threading.Thread(target=download, args=(script,))
            thread.setDaemon(True)
            thread.start()
