import json
import requests
from wetland import config


# sensor name
name = config.cfg.get("wetland", "name")

# urls to report
urls = [v for k, v in config.cfg.items("bearychat") if k.startswith("url")]


class plugin(object):
    def __init__(self, hacker_ip):
        self.hacker_ip = hacker_ip

    def send(self, subject, action, content):
        if subject != 'wetland':
            return False
        if action in ['env_request', 'pty_request', 'global_request',
                      'channel_request']:
            return False

        text = []
        text.append('Sensor:\t%s' % name)
        text.append('Hacker:\t%s' % self.hacker_ip)
        text.append('Action:\t%s' % action)
        text.append('Content:\t%s' % content)

        body = {'text': '\n'.join(text), 'markdown': True,
                'notification':'Wetland Honeypot Report'}
        headers = {"Content-Type": "application/json"}
        data = json.dumps(body)

        for url in urls:
            requests.post(url, headers=headers, data=data)

        return True
