import os
import argparse

valueSet = set(['shell.og', 'reverse.log', 'direct.log', 'exec.log'])

def clear(logs, pwd):
    for ip in os.listdir(logs):
        if not os.path.isdir(os.path.join(logs, ip)):
            continue

        log = os.listdir(os.path.join(logs, ip))

        if 'pwd.log' in log:
            pwd_path = os.path.join(logs, ip, 'pwd.log')
            with open(pwd, 'a') as w, open(pwd_path) as r:
                for i in r.readlines():
                    w.writelines(i.split(" ")[1] + '\n')

        if not len(set(log) & valueSet):
            os.system('rm -rf %s' % os.path.join(logs, ip))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete pwdlog, Leave others')
    parser.add_argument("-p", required=True, help='The path of log folder')
    parser.add_argument("-l", default='pwd.txt', help='The path of pwd file')
    args = parser.parse_args()
    clear(args.p, args.l)
