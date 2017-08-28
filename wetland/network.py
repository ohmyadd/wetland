import os
import IPy
import random
from wetland import config

if config.cfg.get("network", "enable").lower() != 'true':
    class network(object):
        def __init__(self, hacker_ip, docker_ip):
            pass

        def create(self):
            pass

        def delete(self):
            pass
else:
    class network(object):
        def __init__(self, hacker_ip, docker_ip):
            if config.cfg.get("network", "enable").lower() == 'true':
                return 
            self.hacker_ip = IPy.IP(hacker_ip)
            self.docker_ip = IPy.IP(docker_ip)
            self.iface = None
            rand = random.randint(1, 2**32)
            self.fake_ip = IPy.IP((self.hacker_ip.int() + rand) % 2**32)

        def create(self):
            if config.cfg.get("network", "enable").lower() == 'true':
                return 
            self.iface = 'wd'+str(self.hacker_ip).replace(".", "")
            e = 0
            e += os.system("ip link add name %s type dummy" % self.iface)
            e += os.system("ip link set %s up" % self.iface)
            e += os.system("ip addr add %s/32 dev %s" % (self.fake_ip, self.iface))
            e += os.system("iptables -t nat -A POSTROUTING -s %s/32 -d %s/32 "
                           "-p tcp --dport 22 -j SNAT --to %s" % (self.fake_ip,
                                              self.docker_ip, self.hacker_ip))
            e += os.system("iptables -t nat -A PREROUTING -s %s/32 -d %s/32 "
                        "-p tcp --sport 22 -j DNAT --to %s" % (self.docker_ip,
                                              self.hacker_ip, self.fake_ip))
            return True if e == 0 else False

        def delete(self):
            if config.cfg.get("network", "enable").lower() == 'true':
                return 
            e = 0
            e += os.system("ip link del dev %s" % self.iface)
            e += os.system("iptables -t nat -D POSTROUTING -s %s/32 -d %s/32 "
                           "-p tcp --dport 22 -j SNAT --to %s" % (self.fake_ip,
                                              self.docker_ip, self.hacker_ip))
            e += os.system("iptables -t nat -D PREROUTING -s %s/32 -d %s/32 "
                        "-p tcp --sport 22 -j DNAT --to %s" % (self.docker_ip,
                                              self.hacker_ip, self.fake_ip))
            return True if e == 0 else False
