import select
import threading


def reverse_handler(*args):
    t = threading.Thread(target=reverse_handler2, args=(args))
    t.setDaemon(True)
    t.start()


def reverse_handler2(docker_channel, origin, destination, hacker_trans,
                     output):
    try:
        hacker_channel = hacker_trans.open_forwarded_tcpip_channel(origin,
                                                               destination)
    except:
        docker_channel.close()
        return

    output.o('wetland', 'reverse', 'ori:%s, dest:%s' % (origin, destination))
    output.o('content', 'reverse', "N"*20)

    try:
        while True:
            r, w, x = select.select([hacker_channel, docker_channel], [], [])
            if hacker_channel in r:
                text = hacker_channel.recv(1024)
                output.o('content', 'reverse', '[H]:'+text.encode("hex"))
                if len(text) == 0:
                    break
                docker_channel.send(text)

            if docker_channel in r:
                text = docker_channel.recv(1024)
                output.o('content', 'reverse', '[V]:'+text.encode("hex"))
                if len(text) == 0:
                    break
                hacker_channel.send(text)

    except Exception as e:
        print e
    finally:
        hacker_channel.close()
        docker_channel.close()
