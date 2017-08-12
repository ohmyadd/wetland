import time
import yagmail
from wetland import config


class plugin(object):
    def __init__(self):
        self.cfg = config.cfg

        self.user = self.cfg.get("email", "user")
        self.pwd = self.cfg.get("email", "pwd")
        self.host = self.cfg.get("email", "host")
        self.port = self.cfg.getint("email", "port")

        self.tos = []
        for k,v in self.cfg.items("email"):
            if k.startswith("to"):
                self.tos.append(v)

        self.name = self.cfg.get("wetland", "name")
        d = {'info':1, 'warning':2, 'urgent':3}
        self.level = d.get(self.cfg.get('email', 'level'), 2)

    def send(self, level, **kargs):
        if level < self.level:
            return

        subject = "Wetland %s Honeypot Notice" % self.name

        d = {1:'Info', 2:'warning', 3:'Urgent'}
        texts = []
        texts.append("Level:  %s" % d[self.level])

        for k, v in kargs.items():
            texts.append("%s: %s" % (k, v))
        text = '\n'.join(texts)


        for to in self.tos:
            print self.user, self.pwd, self.host, self.port
            client = yagmail.SMTP(user=self.user, password=self.pwd,
                                  host=self.host, port=self.port)
            print 'in'
            client.send(to=to, subject=subject, contents=text)

    def info(self, **kargs):
        self.send(level=1, **kargs)

    def warning(self, **kargs):
        self.send(level=2, **kargs)

    def urgent(self, **kargs):
        self.send(level=3, **kargs)
