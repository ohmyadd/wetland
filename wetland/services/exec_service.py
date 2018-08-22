import re
import os
import uuid
from wetland.config import cfg


def exec_service(hacker_session, docker_session, cmd, output):

    docker_session.exec_command(cmd)
    output.o('content', 'exec', "N"*20)
    output.o('content', 'exec', '[H]:'+cmd.encode("hex"))
    output.o('wetland', 'exec command', cmd)
    if 'wget' in cmd:
        output.downandup(cmd)

    filelen = 0
    nowlen = 0
    if re.match('^scp\s*(-r)?\s*-[t]\s*\S*$', cmd):
        isscp = True
    else:
        isscp = False

    try:
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

    except Exception, e:
        print e
    finally:
        docker_session.close()
        hacker_session.close()
