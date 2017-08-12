import traceback


def shell_service(hacker_session, docker_session, shell_logger, wd_logger):

    hacker_session.settimeout(3600)
    shell_logger.info("N"*20)

    try:
        while True:
            if hacker_session.recv_ready():
                text = hacker_session.recv(1)
                docker_session.sendall(text)
                shell_logger.info('[H]:'+text.encode("hex"))

            if docker_session.recv_ready():
                text = docker_session.recv(1024)
                shell_logger.info('[V]:'+text.encode("hex"))
                hacker_session.sendall(text)

            if docker_session.recv_stderr_ready():
                text = docker_session.recv_stderr(1024)
                hacker_session.sendall_stderr(text)

            if docker_session.eof_received:
                hacker_session.shutdown_write()
                hacker_session.send_exit_status(0)
                break

            if hacker_session.eof_received:
                break

    except Exception, e:
        print e
        traceback.print_exc()
    finally:
        hacker_session.close()
        docker_session.close()
