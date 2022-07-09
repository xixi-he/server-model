#!/usr/bin/python3

import socket
import sys
import time
import select
import threading
from concurrent.futures import ThreadPoolExecutor


# 多线程，线程里用IO多路复用的模式-写法1
# 这个写法相对于thread_pool_select_v2来说，会出现serversocket的抢夺，
# 1. 抢夺可能好一些资源
# 2. 可能出现负载的抖动。但是reuseport是根据ip:port哈希的，每个线程能分配到的连接数肯定是均匀的
def work(serversocket, thread_i):
    r_inputs = set()
    r_inputs.add(serversocket)
    w_inputs = set()
    e_inputs = set()
    # 建立客户端连接
    while True:
        if not (len(r_inputs) == 0 and len(r_inputs) == 0 and len(r_inputs) == 0):
            print("thread %d: r_inputs=%d, w_inputs=%d, e_inputs=%d" % (thread_i, len(r_inputs), len(w_inputs), len(e_inputs)))
        r_list, w_list, e_list = select.select(r_inputs, w_inputs, e_inputs, 1)
        print("thread %d: r_list=%d, w_list=%d, e_list=%d" % (thread_i, len(r_list), len(w_list), len(e_list)))
        for r in r_list:
            # 如果这个可读的IO正好是服务端用来Listen的IO，说明是新的连接过来了，要创建连接
            if r == serversocket:
                try:
                    clientsocket, addr = r.accept()
                    print("thread %d: got new connection, addr=%s" % (thread_i, str(addr)))
                    clientsocket.setblocking(False)  # 非阻塞IO
                    r_inputs.add(clientsocket)
                    w_inputs.add(clientsocket)
                    e_inputs.add(clientsocket)
                except: # 因为listen socket全局只有一个，所以多线程会竞争，这里检查到了ready，但是accept的时候已经被其他的给accept了
                    print("thread %d: already accept" % thread_i)
            else:  # 说明是普通连接的IO可读了
                msg = r.recv(1024)
                if msg:
                    print("thread %d: got %s" % (thread_i, msg))
                else:
                    print("thread %d: 对端断开连接" % thread_i)
                    # 把结束的事件移除
                    tmp_list = set()
                    for tmp in r_inputs:
                        if tmp != r:
                            tmp_list.add(tmp)
                    r_inputs = tmp_list
        for w in w_list:
            cnt = 0  # 模拟占CPU的操作
            for i in range(500):
                cnt += i
            msg = "thread %d: send to data %d" % (thread_i, cnt)
            print(msg)
            w.send(msg.encode())
            # w.close()
            # 把结束的事件移除
            tmp_list = set()
            for tmp in w_inputs:
                if tmp != w:
                    tmp_list.add(tmp)
                w_inputs = tmp_list
        if len(e_list) > 0:  # 产生了错误的事件，即连接错误
            print(e_list)
            e_inputs.clear()
        print("\n")


def main():
    # thread_pool = ThreadPoolExecutor(10)
    r_inputs = set()
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 获取本地主机名
    host = socket.gethostname()
    port = 19999
    serversocket.bind((host, port))
    # 设置最大连接数，超过后排队
    serversocket.listen(5)
    serversocket.setblocking(False)  # 非阻塞IO
    r_inputs.add(serversocket)  # listen的socket只有读事件，不会去写

    ts = []
    for i in range(3):
        # 这个写法相对于thread_pool_select_v2来说，会出现serversocket的抢夺，
        # 1. 抢夺可能好一些资源
        # 2. 可能出现负载的抖动。但是reuseport是根据ip:port哈希的，每个线程能分配到的连接数肯定是均匀的
        t = threading.Thread(target=work, args=(serversocket, i))
        t.start()
        ts.append(t)

    # 可以提前创建好一些线程，主线程继续serversocket.accept(), 然后把clientsocket放入队列里，线程去取？
    # 不可行，因为这样的话线程需要两个等待操作：select等待已经建好的连接的可读写事件、等待队列里的数据。
    # 这两个都是阻塞的，会互相影响对方


main()