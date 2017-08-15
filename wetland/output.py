import threading
from wetland import config
from importlib import import_module as impt


def get_plugins():
    pname = []
    for k, v in config.cfg.items('output'):
        if v == 'true':
            pname.append(k)
    return pname


pname = get_plugins()


class output(object):
    def __init__(self, hacker_ip):
        self.hacker_ip = hacker_ip
        self.plugins = [impt('wetland.output_plugin.'+n).plugin(self.hacker_ip)
                        for n in pname]

    def o(self, *args):
        for p in self.plugins:
            thread = threading.Thread(target=p.send, args=args)
            thread.setDaemon(True)
            thread.start()
