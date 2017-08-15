import yagmail
from wetland import config

# sensor name
name = config.cfg.get("wetland", "name")

# smtp
user = config.cfg.get("email", "user")
pwd = config.cfg.get("email", "pwd")
host = config.cfg.get("email", "host")
port = config.cfg.getint("email", "port")

# receviers
tos = [v for k, v in config.cfg.items("email") if k.startswith("to")]


class plugin(object):
    def __init__(self, hacker_ip):
        self.hacker_ip = hacker_ip

    def send(self, subject, action, content):
        if subject != 'wetland':
            return False

        subject = "Wetland %s Honeypot" % name

        text = []
        text.append('Sensor:\t%s' % name)
        text.append('Hacker:\t%s' % self.hacker_ip)
        text.append('Action:\t%s' % action)
        text.append('Content:\t%s' % content)

        for to in self.tos:
            print self.user, self.pwd, self.host, self.port
            client = yagmail.SMTP(user=self.user, password=self.pwd,
                                  host=self.host, port=self.port)
            client.send(to=to, subject=subject, contents='\n'.join(text))
