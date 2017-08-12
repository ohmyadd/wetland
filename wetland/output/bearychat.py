import json
import time
import requests
from wetland import config


class plugin(object):
    def __init__(self):
        self.cfg = config.cfg

        self.urls = []
        for k,v in self.cfg.items("bearychat"):
            if k.startswith("url"):
                self.urls.append(v)
        self.heng = '**' + '='*22 + '**'
        self.name = self.cfg.get("wetland", "name")

        d = {'info':1, 'warning':2, 'urgent':3}
        self.level = d.get(self.cfg.get('bearychat', 'level'), 2)

    def send(self, level, **kargs):
        if level < self.level:
            return

        text = '\n'.join([self.heng, self.name, self.heng])
        body = {'text':text, 'markdown':True, 'attachments':[]}

        d = {1:'Info', 2:'Warning', 3:'Urgent'}
        body['attachments'].append({'title':'Level', 'text':d[level]})

        for k, v in kargs.items():
            tmp = {'title':k, 'text':v}
            body['attachments'].append(tmp)

        for url in self.urls:
            requests.post(url, headers={"Content-Type":"application/json"},
                          data=json.dumps(body))

    def info(self, **kargs):
        self.send(level=1, **kargs)

    def warning(self, **kargs):
        self.send(level=2, **kargs)

    def urgent(self, **kargs):
        self.send(level=3, **kargs)
