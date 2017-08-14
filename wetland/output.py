import threading
from wetland import config
from importlib import import_module as impt

def get_plugins():
    pname = []
    for k, v in config.cfg.items('output'):
        if v == 'true':
            pname.append(k)
    return pname

plugins = [impt('wetland.output.'+n).plugin() for n in get_plugins()]

def sub(level='warning', **kargs):
    for p in plugins:
        getattr(p, level)(**kargs)

def output1(**kargs):
    thread = threading.Thread(target=sub, kwargs=kargs)
    thread.setDaemon(True)
    thread.start()

def output(kind, subject, action, content):
    print kind, subject, action, content
