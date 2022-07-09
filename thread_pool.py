#!/usr/bin/python3

import socket
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor


# 线程池模式，优点（对比于每个请求创建一个线程的方式）：
# 1. 线程可以复用，不随着连接结束而退出，然后新连接又创建
# 2. 可以很好控制最大线程数（ThreadPoolExecutor帮忙做）

# 缺点：
# 当前的这种线程池写法：单个线程内部还是阻塞的，不能同时处理多个连接。必须等待上一个连接结束后，再处理下一个连接。
# 性能和资源利用率都不行

def work(sock, addr):
    msg = sock.recv(64)
    print("got %s" % msg.decode())
    print("连接地址: %s" % str(addr))
    time.sleep(1)
    msg = str(addr) + ' i got u！' + "\r\n"
    sock.send(msg.encode('utf-8'))
    sock.close()


def main():
    thread_pool = ThreadPoolExecutor(3)
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 获取本地主机名
    host = socket.gethostname()
    print(host)

    port = 19999

    serversocket.bind((host, port))

    # 设置最大连接数，超过后排队
    serversocket.listen(5)

    while True:
        # 建立客户端连接
        clientsocket, addr = serversocket.accept()
        # msg = clientsocket.recv(64)
        # print("got %s" % msg.decode())
        # print("连接地址: %s" % str(addr))
        # work(clientsocket, addr)

        thread_pool.submit(work, clientsocket, addr)

main()