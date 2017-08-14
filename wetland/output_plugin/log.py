import os
import logging
from wetland import config


class loggers():
    def __init__(self):
        self.cfg = config.cfg
        self.logpath = self.cfg.get("log", "wetland")
        if not os.path.exists(self.logpath):
            os.makedirs(self.logpath)

    def get(self, kind, src_ip):
        if kind not in ['pwd', 'shell', 'exec', 'direct', 'reverse', 'sftp']:
            return None

        logger = logging.getLogger(':'.join((kind, src_ip)))
        logger.setLevel(logging.INFO)
        if logger.handlers:
            return logger

        filename = os.path.join(self.logpath, src_ip, kind+'.log')
        filepath = os.path.dirname(filename)
        if not os.path.exists(filepath):
            os.makedirs(filepath)

        handler = logging.FileHandler(filename=filename)
        formatter = logging.Formatter('%(asctime)s  %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def get2(self, name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        hd = logging.FileHandler(os.path.join(self.logpath, 'wetland.log'))
        ft = logging.Formatter('%(asctime)s %(filename)s %(module)s %(message)s')
        hd.setFormatter(ft)
        logger.addHandler(hd)
        return logger
