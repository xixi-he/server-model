#!/usr/bin/python3

import socket
import sys
import time
import select


# # 单线程非阻塞IO模式的错误写法：主socket没有设置成非阻塞让select监控，那么虽然实际连接的socket是非阻塞的，
# 但一旦进入下一个Loop，如果没有新连接过来，就会一直卡在accept里
# def main():
#     r_inputs = set()
#     w_inputs = set()
#     e_inputs = set()
#     serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#
#     # 获取本地主机名
#     host = socket.gethostname()
#     port = 19999
#     serversocket.bind((host, port))
#     # 设置最大连接数，超过后排队
#     serversocket.listen(5)
#
#     while True:
#         # 建立客户端连接
#         print("loop")
#         clientsocket, addr = serversocket.accept()
#         clientsocket.setblocking(False)  # 非阻塞IO
#         r_inputs.add(clientsocket)
#         w_inputs.add(clientsocket)
#         e_inputs.add(clientsocket)
#         print("r_inputs=%d, w_inputs=%d, e_inputs=%d" % (len(r_inputs), len(w_inputs), len(e_inputs)))
#         r_list, w_list, e_list = select.select(r_inputs, w_inputs, e_inputs, 1)
#         print("r_list=%d, w_list=%d, e_list=%d" % (len(r_list), len(w_list), len(e_list)))
#         for r in r_list:
#             msg = r.recv(1024)
#             if msg:
#                 print("got %s" % msg)
#             else:
#                 print("对端断开连接")
#                 # 把结束的事件移除
#                 tmp_list = set()
#                 for tmp in r_inputs:
#                     if tmp != r:
#                         tmp_list.add(tmp)
#                 r_inputs = tmp_list
#         for w in w_list:
#             msg = "send to data"
#             print(msg)
#             w.send(msg.encode())
#             # w.close()
#             # 把结束的事件移除
#             tmp_list = set()
#             for tmp in w_inputs:
#                 if tmp != w:
#                     tmp_list.add(tmp)
#                 w_inputs = tmp_list
#         if len(e_list) > 0:  # 产生了错误的事件，即连接错误
#             print(e_list)
#             e_inputs.clear()

# 单线程非阻塞IO模式正确写法。主socket和客户端socket都非阻塞，让select监控。
# 注意下，客户端连接的读写事件完成后，要不要sock.close()，如果不得话会怎么样。自己研究下
# 目前这么写，服务端和客户端都没有报错，客户端执行完也退出程序了。但是可能连接还在？或者fd会泄露？
# 无论连接情况如何，服务端都要close告诉内核去释放fd。只是可能python自动帮忙干了？
# 问题：如果不把已经处理好的socket从r_inputs/w_inputs移除会怎么样？
# 可以通过客户端随机找一个连接，sleep超长时间，来看会不会阻塞其他请求。（不会哈哈）
# 这样就实现了IO多路复用技术。在单个线程里，可以不受单个连接阻塞，”并发”处理多个连接。
# 实际上不同连接的、socket的IO还是独立的，并没有“复用”，只是内核提供了一个可以询问的系统调用：select/poll/epoll。
# IO本身没有变化，只是能用较少的代价监控大量IO事件（想一想，如果没有select，要怎么写。也是死循环，尝试读写每个socket，如果错误跳过，如果能读写就读写。 那比select差在哪里呢）
# 实现关键点：非阻塞IO+select
# 非阻塞IO就让线程不会阻塞，但是怎么能知道某个IO可以用了，然后让对应的连接去处理呢？就需要select
# 提前把要监听的socket准备好，一个死循环去调用select询问就行了。如果没有任何事件ok，select不会返回。只要有一个ok, 才会返回
# 从服务端日志也可以看出，这里处理流程就是：任何一个IO准备好，select就返回，然后线程去处理
# 如果有多个并发请求过来，一般都是某个连接的IO好了，然后下一个loop，下个连接的IO好了，然后下一个loop，又是某个连接的IO好了
# IO好得很快，所以感觉就是不同连接，大家你来我往，线程雨露均沾，一会你一会我。
def main():
    r_inputs = set()
    w_inputs = set()
    e_inputs = set()
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

    while True:
        # 建立客户端连接
        print("loop")
        if not(len(r_inputs) == 0 and len(r_inputs) == 0 and len(r_inputs) == 0):
            print("r_inputs=%d, w_inputs=%d, e_inputs=%d" % (len(r_inputs), len(w_inputs), len(e_inputs)))
        r_list, w_list, e_list = select.select(r_inputs, w_inputs, e_inputs, 1)
        print("r_list=%d, w_list=%d, e_list=%d" % (len(r_list), len(w_list), len(e_list)))
        for r in r_list:
            # 如果这个可读的IO正好是服务端用来Listen的IO，说明是新的连接过来了，要创建连接
            if r == serversocket:
                clientsocket, addr = r.accept()
                print("got new connection, addr=%s" % str(addr))
                clientsocket.setblocking(False)  # 非阻塞IO
                r_inputs.add(clientsocket)
                w_inputs.add(clientsocket)
                e_inputs.add(clientsocket)
            else:   # 说明是普通连接的IO可读了
                msg = r.recv(1024)
                if msg:
                    print("got %s" % msg)
                else:
                    print("对端断开连接")
                    # 把结束的事件移除
                    tmp_list = set()
                    for tmp in r_inputs:
                        if tmp != r:
                            tmp_list.add(tmp)
                    r_inputs = tmp_list
        for w in w_list:
            cnt = 0 # 模拟占CPU的操作
            for i in range(500):
                cnt += i
            msg = "send to data %d" % cnt
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


main()