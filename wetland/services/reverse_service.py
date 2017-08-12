import select
import threading
import traceback


def reverse_handler(*args):
    t = threading.Thread(target=reverse_handler2, args=(args))
    t.setDaemon(True)
    t.start()


def reverse_handler2(docker_channel, origin, destination, hacker_trans,
                    reverse_logger, wd_logger):
    try:
        hacker_channel = hacker_trans.open_forwarded_tcpip_channel(origin,
                                                               destination)
    except:
        docker_channel.close()
        return

    reverse_logger.info("N"*20)

    try:
        while True:
            r, w, x = select.select([hacker_channel, docker_channel], [], [])
            if hacker_channel in r:
                text = hacker_channel.recv(1024)
                reverse_logger.info('[H]:'+text.encode("hex"))
                if len(text) == 0:
                    break
                docker_channel.send(text)

            if docker_channel in r:
                text = docker_channel.recv(1024)
                reverse_logger.info('[V]:'+text.encode("hex"))
                if len(text) == 0:
                    break
                hacker_channel.send(text)

    except:
        traceback.print_exc()
    finally:
        hacker_channel.close()
        docker_channel.close()
