import os
import json
import select

with open(os.path.join(os.path.dirname(__file__), 'visual.txt')) as txt:
    visual = json.load(txt)


def shell_service(hacker_session, docker_session, output):

    hacker_session.settimeout(3600)
    output.o('content', 'shell', "N"*20)

    hacker_fileno = hacker_session.fileno()
    docker_fileno = docker_session.fileno()

    epoll = select.epoll()
    epoll.register(hacker_fileno, select.EPOLLIN)
    epoll.register(docker_fileno, select.EPOLLIN)

    try:
        command = []
        while True:
            events = epoll.poll()

            for fd, event in events:
                if fd == hacker_fileno:

                    if event & select.EPOLLIN:
                        if hacker_session.recv_ready():
                            text = hacker_session.recv(1)
                            docker_session.sendall(text)
                            output.o('content', 'shell',
                                     '[H]:'+text.encode("hex"))
                            if text == '\r':
                                cmd = ''.join(command)
                                output.o('wetland', 'shell command', cmd)
                                command = []
                            elif text == '\x7f' and command:
                                command.pop()
                            else:
                                command.append(visual[text])
                        if hacker_session.eof_received:
                            docker_session.shutdown_write()
                            docker_session.send_exit_status(0)
                    elif event & select.EPOLLHUP:
                        break

                elif fd == docker_fileno:
                    if event & select.EPOLLIN:
                        if docker_session.recv_ready():
                            text = docker_session.recv(1024)
                            output.o('content', 'shell',
                                     '[V]:'+text.encode("hex"))
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

    except Exception, e:
        print e
    finally:
        hacker_session.close()
        docker_session.close()
