import re
import os
import uuid
import select
from wetland.config import cfg


def exec_service(hacker_session, docker_session, cmd, output):

    hacker_fileno = hacker_session.fileno()
    docker_fileno = docker_session.fileno()

    epoll = select.epoll()
    epoll.register(hacker_fileno, select.EPOLLIN)
    epoll.register(docker_fileno, select.EPOLLIN)

    docker_session.exec_command(cmd)
    output.o('content', 'exec', "N"*20)
    output.o('content', 'exec', '[H]:'+cmd.encode("hex"))
    output.o('wetland', 'exec command', cmd)

    filelen = 0
    nowlen = 0
    if re.match('^scp\s*(-r)?\s*-[t]\s*\S*$', cmd):
        isscp = True
    else:
        isscp = False

    try:
        while True:
            events = epoll.poll()

            for fd, event in events:
                if fd == hacker_fileno:

                    if event & select.EPOLLIN:
                        if hacker_session.recv_ready():
                            text = hacker_session.recv(1024)

                            if not isscp:
                                output.o('content', 'exec', '[H]:'+text.encode("hex"))
                                output.o('wetland', 'exec command', text)
                            else:
                                if re.match('^C\d{4}\s+\d+\s+\S+\n$', text):
                                    filename = str(uuid.uuid1()).replace('-', '')
                                    filepath = os.path.join(cfg.get('files', 'path'),
                                                            filename)
                                    scpfile = open(filepath, 'wb')
                                    filelen = int(text.split(' ')[1])
                                else:
                                    if nowlen >= filelen:
                                        pass
                                    else:
                                        scpfile.write(text)
                                        nowlen += len(text)
                                        if nowlen >= filelen:
                                            scpfile.close()
                                            nowlen = 0
                                            filelen = 0
                                            output.o('upfile', 'scp', filename)
                                            output.upfile(filename)

                            # print 'hacker said: ', text.encode("hex"), text
                            docker_session.sendall(text)
                        if hacker_session.eof_received:
                            docker_session.shutdown_write()
                            docker_session.send_exit_status(0)

                    elif event & select.EPOLLHUP:
                        break

                elif fd == docker_fileno:
                    if event & select.EPOLLIN:

                        if docker_session.recv_ready():
                            text = docker_session.recv(1024)
                            output.o('content', 'exec',
                                     '[V]:'+text.encode("hex"))
                            # print 'docker said: ', text.encode("hex"), text
                            hacker_session.sendall(text)

                        if docker_session.recv_stderr_ready():
                            text = docker_session.recv_stderr(1024)
                            hacker_session.sendall_stderr(text)

                        if docker_session.eof_received:
                            hacker_session.shutdown_write()
                            hacker_session.send_exit_status(0)

                    elif event & select.EPOLLHUP:
                        break

            if docker_session.eof_received or hacker_session.eof_received:
                break

        """
        while True:
            if hacker_session.recv_ready():
                text = hacker_session.recv(1024)

                if not isscp:
                    output.o('content', 'exec', '[H]:'+text.encode("hex"))
                    output.o('wetland', 'exec command', text)
                else:
                    if re.match('^C\d{4}\s+\d+\s+\S+\n$', text):
                        filename = str(uuid.uuid1()).replace('-', '')
                        filepath = os.path.join(cfg.get('files', 'path'),
                                                filename)
                        scpfile = open(filepath, 'wb')
                        filelen = int(text.split(' ')[1])
                    else:
                        if nowlen >= filelen:
                            pass
                        else:
                            scpfile.write(text)
                            nowlen += len(text)
                            if nowlen >= filelen:
                                scpfile.close()
                                nowlen = 0
                                filelen = 0
                                output.o('upfile', 'scp', filename)
                                output.upfile(filename)

                # print 'hacker said: ', text.encode("hex"), text
                docker_session.sendall(text)

            if docker_session.recv_ready():
                text = docker_session.recv(1024)
                output.o('content', 'exec', '[V]:'+text.encode("hex"))
                # print 'docker said: ', text.encode("hex"), text
                hacker_session.sendall(text)

            if docker_session.recv_stderr_ready():
                text = docker_session.recv_stderr(1024)
                hacker_session.sendall_stderr(text)

            if docker_session.eof_received:
                hacker_session.shutdown_write()
                hacker_session.send_exit_status(0)

            if hacker_session.eof_received:
                docker_session.shutdown_write()
                docker_session.send_exit_status(0)

            if hacker_session.eof_received or docker_session.eof_received:
                break
        """

    except Exception, e:
        print e
    finally:
        docker_session.close()
        hacker_session.close()

        with open('/var/cache/.url', 'a+') as txt:
            urls = txt.read()
            if urls:
                output.o('wetland', 'download',
                         [i for i in urls.split('\n') if i])
        if urls:
            os.system('cat /dev/null > /var/cache/.url')
