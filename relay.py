#!/usr/bin/env python3
import logging
import queue
import socket
import threading


lock = threading.Lock()
logging.basicConfig(
        format='%(asctime)-15s %(clientip)-15s %(call)-8s %(message)s')
logger = logging.getLogger('telnetrelay')
logger.setLevel(logging.INFO)
clients = []


class RelayServer(threading.Thread):
    def __init__(self, info):
        threading.Thread.__init__(self)
        self.socket = info[0]
        self.address = info[1]
        self.loginfo = {'clientip': self.address[0], 'call': '---'}
        self.queue = queue.Queue()

    def run(self):
        lock.acquire()
        clients.append(self)
        lock.release()
        logger.info('new connection', extra=self.loginfo)
        if not self.login():
            return
        self.loop()

    def login(self):
        self.socket.send(b'Please enter your call: ')
        call = self.socket.recv(20)
        if not call:
            return False
        self.loginfo['call'] = call.decode('utf-8').strip()
        logger.info('logged in', extra=self.loginfo)
        self.socket.send(b'>\r\n\r\n')
        return True

    def loop(self):
        while True:
            spot = self.queue.get()
            try:
                self.socket.send(spot + b'\r\n')
            except:
                self.terminate()
                break

    def terminate(self):
        lock.acquire()
        clients.remove(self)
        lock.release()
        logger.info('logged out', extra=self.loginfo)
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            pass

    def sendSpot(self, spot):
        self.queue.put(spot)


class RelayClient(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.skt.connect(('telnet.reversebeacon.net', 7000))
        self.login()
        self.loop()

    def login(self):
        msg = self.skt.recv(1024)
        self.skt.send(b'PD7LOL\r\n')
        self.skt.recv(1024)

    def loop(self):
        loginfo = {'clientip': '', 'call': ''}
        while True:
            spots = self.skt.recv(1024)
            for spot in spots.split(b'\r\n'):
                spot = spot.strip()
                if spot == b'':
                    continue
                loginfo['clientip'] = len(clients)
                logger.info(spot.decode('utf-8'), extra=loginfo)
                lock.acquire()
                for client in clients:
                    client.sendSpot(spot)
                lock.release()


if __name__ == '__main__':
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.bind(('', 7000))
    skt.listen(4)

    client = RelayClient()
    client.start()

    while True:
        RelayServer(skt.accept()).start()
