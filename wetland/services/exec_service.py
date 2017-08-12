import traceback
from socket import error as socket_error


def exec_service(hacker_session, docker_session, cmd, exec_logger, wd_logger):

    docker_session.exec_command(cmd)
    exec_logger.info("N"*20)
    exec_logger.info('[H]:'+cmd.encode("hex"))

    try:
        while True:
            if hacker_session.recv_ready():
                text = hacker_session.recv(1024)
                exec_logger.info('[H]:'+text.encode("hex"))
                print 'hacker said: ', text.encode("hex"), text
                docker_session.sendall(text)
                continue

            if docker_session.recv_ready():
                text = docker_session.recv(1024)
                exec_logger.info('[V]:'+text.encode("hex"))
                print 'docker said: ', text.encode("hex"), text
                hacker_session.sendall(text)
                continue

            if docker_session.recv_stderr_ready():
                text = docker_session.recv_stderr(1024)
                hacker_session.sendall_stderr(text)
                continue

            if hacker_session.eof_received:
                print 'hacker eof recv'
                hacker_session.shutdown_write()
                hacker_session.send_exit_status(0)
                break

            if docker_session.eof_received:
                print 'docker eof recv'
                hacker_session.shutdown_write()
                hacker_session.send_exit_status(0)
                break

    except Exception, e:
        print e
        traceback.print_exc()

    finally:
        docker_session.close()
        hacker_session.close()
