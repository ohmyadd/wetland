import time
import select


def direct_service(hacker_channel_id, hacker_trans, docker_channel, output):

    for i in range(10):
        if hacker_trans._channels.get(hacker_channel_id):
            break
        time.sleep(1)
    else:
        # print 'direct wait for channel timeout'
        docker_channel.close()
        return

    hacker_channel = hacker_trans._channels.get(hacker_channel_id)
    output.o('content', 'direct', "N"*20)

    try:
        while True:

            r, w, x = select.select([hacker_channel, docker_channel], [], [])
            if hacker_channel in r:
                text = hacker_channel.recv(1024)
                output.o('content', 'direct', '[H]:'+text.encode("hex"))
                if len(text) == 0:
                    break
                docker_channel.send(text)

            if docker_channel in r:
                text = docker_channel.recv(1024)
                output.o('content', 'direct', '[V]:'+text.encode("hex"))
                if len(text) == 0:
                    break
                hacker_channel.send(text)

    except Exception, e:
        print e
    finally:
        hacker_channel.close()
        docker_channel.close()
