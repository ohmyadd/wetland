import os
import time
import argparse

valueSet = set(['shell.og', 'reverse.log', 'direct.log', 'exec.log'])


def clear(logs_path, pwd):
    for ip in os.listdir(logs_path):
        if not os.path.isdir(os.path.join(logs_path, ip)):
            continue

        log = os.listdir(os.path.join(logs_path, ip))

        if 'pwd.log' in log:
            pwd_path = os.path.join(logs_path, ip, 'pwd.log')
            with open(pwd, 'a') as w, open(pwd_path) as r:
                for i in r.readlines():
                    w.writelines(i.split(" ")[1] + '\n')

        if (not len(set(log) & valueSet)) and ip != 'sftp':
            os.system('rm -rf %s' % os.path.join(logs_path, ip))


def summary(logs_path):
    timeformat = '%y%m%d-%H:%M'
    summary_log = open(os.path.join(logs_path, 'summary.txt'), 'w')

    for root, dirs, files in os.walk(logs_path):
        if root == logs_path:
            continue

        summary_log.write(root + '\n')
        for f in files:
            p = os.path.join(root, f)
            t = time.strftime(timeformat, time.localtime(os.stat(p).st_mtime))
            s = os.stat(p).st_size/1024.0
            if s < 1:
                summary_log.write('\t%s %.2fkb \t%s\n' % (t, s, f))
            else:
                summary_log.write('\t%s %dkb \t %s\n' % (t, s, f))

    summary_log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete pwdlog, Leave others')
    parser.add_argument("p", help='The path of log folder')
    parser.add_argument("-l", help='The path of pwd file')
    args = parser.parse_args()
    if not args.l:
        args.l = os.path.join(args.p, 'pwd.txt')

    clear(args.p, args.l)
    summary(args.p)
