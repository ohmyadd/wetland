import os
import re
import sys
import argparse
from collections import deque


class shell_player(object):

    def __init__(self, filename):
        self.filename = filename

    def get(self):
        shell_sessions = []
        with open(self.filename) as log_file:
            datas = []
            for i in log_file.xreadlines():
                a = i.strip().split(" ")

                timestamp = a[0]
                data = a[1]
                if ':' in data:
                    data = data.split(":")
                    datas.append((timestamp, data[0], data[1].decode("hex")))
                elif data == 'NNNNNNNNNNNNNNNNNNNN':
                    if datas:
                        shell_sessions.append(datas)
                        datas = []
            shell_sessions.append(datas)
        self.sessions = shell_sessions

    def play(self, datas):
        startstamp = datas[0][0]
        endstamp = datas[-1][0]

        print """
        ============================================================
        ========= Session start at %s =========
        ========= Session close at %s =========
        ============================================================
        """ % (startstamp, endstamp)

        for data in datas:
            direction = data[1]
            text = data[2]

            if direction == '[V]':
                sys.stdout.write(text.lstrip('\r\n'))

            elif direction == '[H]' and text == '\r':
                raw_input()
        print """
        =================================================
        ============= Session closed ====================
        ================================================= """ 
    def start(self):
        self.get()

        print '[+] Detect %d sessions' % len(self.sessions)

        for n, i in enumerate(self.sessions):
            print '[%d] %s =====> %s' % (n, self.sessions[n][0][0],
                                         self.sessions[n][-1][0])

        try:
            index = int(raw_input("\n[+] which one do you want to replay? "))
            os.system("clear")
            self.play(self.sessions[index])
        except Exception, e:
            print e


class exec_player(object):
    def __init__(self, filename, save_path):
        self.filename = filename
        self.save_path = save_path

    def get(self):
        exec_sessions = []
        with open(self.filename) as log_file:
            datas = []
            for i in log_file.xreadlines():
                a = i.strip().split(" ")

                timestamp = a[0]
                data = a[1]
                if ':' in data:
                    data = data.split(":")
                    datas.append((timestamp, data[0], data[1].decode("hex")))
                elif data == 'NNNNNNNNNNNNNNNNNNNN':
                    if datas:
                        if re.match('^scp\s*(-r)?\s*-[ft]\s*\S*$', datas[0][2]):
                            self.scp(datas)
                            datas = []
                        else:
                            exec_sessions.append(datas)
                            datas = []

            if re.match('^scp\s*(-r)?\s*-[ft]\s*\S*$', datas[0][2]):
                self.scp(datas)
            else:
                exec_sessions.append(datas)
        self.sessions = exec_sessions

    def start(self):
        self.get()
        print '[+] Detect %d sessions' % len(self.sessions)

        for n, session in enumerate(self.sessions):
            print '[%d] %s =====> %s' % (n, self.sessions[n][0][0],
                                         self.sessions[n][-1][0])
            for s in session:
                if s[1] == '[H]':
                    print '--------------------------- Hacker send----------------------------'
                if s[1] == '[V]':
                    print '--------------------------- Docker send----------------------------'
                print s[2]

    def scp(self, datas):
        t = re.split('\s+', datas[0][2])
        datas.remove(datas[0])
        datas.remove(datas[0])
        dq = deque()

        if '-f' in t:
            if '-r' in t:
                print '[+] Detect scp download folder at ===> %s' % t[-1]
            else:
                print '[+] Detect scp upload   file   at ===> %s' % t[-1]
            dq = deque([i[2] for i in datas if i[1]=='[V]'])
        elif '-t' in t:
            if '-r' in t:
                print '[+] Detect scp upload   folder at ===> %s' % t[-1]
            else:
                print '[+] Detect scp download file   at ===> %s' % t[-1]
            dq = deque([i[2] for i in datas if i[1]=='[H]'])
        else:
            print '[-] scp protocol invalid'

        f = self.extract_files(dq)
        if f:
            self.save_files(f, self.save_path)

    def extract_files(self, datas):

        f = {}
        while datas and datas[0] != 'E\n':
            hdr = datas.popleft()
            name = hdr.strip().split(' ')[2]
            length = int(hdr.strip().split(' ')[1])

            if re.match('^D\d{4}\s+\d+\s+\S+\n$', hdr):
                sub_dict = self.extract_files(datas)
                if sub_dict is None:
                    return None
                f[name] = sub_dict
                tail = datas.popleft()
                if tail != 'E\n':
                    print '[-] scp tail error'
                    return None

            elif re.match('^C\d{4}\s+\d+\s+\S+\n$', hdr):
                contents = []
                while True:
                    tmp = datas.popleft()
                    if tmp == '\x00':
                        break

                    if tmp.endswith('\x00') and  \
                            (len(''.join(contents)) + len(tmp) - 1 == length):
                        contents.append(tmp[:-1])
                        break

                    contents.append(tmp)
                f[name] = ''.join(contents)
            else:
                print '[-] scp head error'
                return None
                break
        return f

    def save_files(self, file_dict, root_path):
        if not os.path.exists(root_path):
            os.makedirs(root_path)

        for name, content in file_dict.items():
            name = re.sub('[^A-Za-z0-9]', '-', name)
            new_path = os.path.join(root_path, name)

            if isinstance(content, str):
                with open(new_path, 'wb') as f:
                    f.write(content)

            elif isinstance(content, dict):
                self.save_files(file_dict[name], os.path.join(root_path, name))

            else:
                return None


class forward_player(object):
    def __init__(self, filename):
        self.filename = filename

    def start(self):
        self.get()
        print '[+] Detect %d sessions' % len(self.sessions)
        for session in self.sessions:
            print '\n\n================================ New session =============================='
            print '======= %s -------> %s ==========' % (session[0][0], session[-1][0])
            print '==========================================================================='
            for s in session:
                if s[1] == '[H]':
                    print '----------------------------- Hacker send------------------------------'
                if s[1] == '[V]':
                    print '----------------------------- Docker send------------------------------'
                print s[2]

    def get(self):
        forward_sessions = []
        with open(self.filename) as log_file:
            datas = []
            for i in log_file.xreadlines():
                a = i.strip().split(" ")

                timestamp = a[0]
                data = a[1]
                if ':' in data:
                    data = data.split(":")
                    datas.append((timestamp, data[0], data[1].decode("hex")))
                elif data == 'NNNNNNNNNNNNNNNNNNNN':
                    if datas:
                        forward_sessions.append(datas)
                        datas = []

            forward_sessions.append(datas)
        self.sessions = forward_sessions


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replay the logs of wetlan')
    parser.add_argument('-t', choices=['shell', 'exec', 'forward'],
                        default='filetype', help='Type of the log file')
    parser.add_argument("p", help='The path of log file')
    parser.add_argument("-s", default='../download/scp',
                        help='Extract file to this folder in exec logs')
    args = parser.parse_args()

    if args.t == 'filetype':
        t = os.path.splitext(os.path.split(args.p)[1])[0]
        if t not in ['shell', 'exec', 'direct', 'reverse']:
            print '[-] filename unknow or you should specify arguemnt -t'
            sys.exit(0)
        args.t = t

    if args.t == 'shell':
        a = shell_player(args.p)
    elif args.t == 'exec':
        a = exec_player(args.p, args.s)
    elif args.t in ['forward', 'direct', 'reverse']:
        a = forward_player(args.p)
    a.start()
