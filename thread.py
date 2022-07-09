#!/usr/bin/python3

import socket
import sys
import time
import threading


# 每个连接一个线程的模式，缺点：
# 1. 每个连接都对应线程的创建和销毁
# 2. 如果连接数几万个，不可能创建几万个线程，还需要限制线程数
def work(sock, addr):
    msg = sock.recv(64)
    print("got %s" % msg.decode())
    print("连接地址: %s" % str(addr))
    time.sleep(1)
    msg = str(addr) + ' i got u！' + "\r\n"
    sock.send(msg.encode('utf-8'))
    sock.close()


def main():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 不经过time_wait，直接关闭

    # 获取本地主机名
    host = socket.gethostname()
    print(host)

    port = 19999

    serversocket.bind((host, port))

    # 设置最大连接数，超过后排队
    serversocket.listen(5)

    while True:
        # 建立客户端连接
        clientsocket, addr = serversocket.accept()  # 为什么这里accept之后得到的socket，被传给work后，能继续accept，不等work执行完
        # 因为accpet返回的是另一个socket，和serversocket不是同一个东西
        # 所有完成了三次握手的连接放入等待队列，accept就是从这个队列里取出连接，然后创建要给新的socket用来和这个连接通信
        # msg = clientsocket.recv(64)
        # print("got %s" % msg.decode())
        # print("连接地址: %s" % str(addr))
        # work(clientsocket, addr)

        t = threading.Thread(target=work, args=(clientsocket, addr))
        t.start()

main()