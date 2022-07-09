# import urllib.request
#
# url = 'http://127.0.0.1:19999'
# res = urllib.request.urlopen(url).read()
# print(res)
# 这个写法会：http.client.BadStatusLine


#!/usr/bin/python3
import socket
import sys
import time
import threading


def request(i):
    # 创建 socket 对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 获取本地主机名
    host = socket.gethostname()
    # 设置端口号
    port = 19999
    # 连接服务，指定主机和端口
    s.connect((host, port))
    time.sleep(1)
    if i == 1:
        time.sleep(5)
    msg = "client hello: %d" % i
    print(msg)
    s.send(msg.encode())
    # 接收小于 1024 字节的数据
    msg = s.recv(1024)
    s.close()
    print ("in %d, recv=%s" % (i, msg.decode()))



def main():
    ts = []
    for i in range(6):
        t = threading.Thread(target=request, args=(i,))
        t.setDaemon(True)
        t.start()
        ts.append(t)
    for t in ts:
        t.join()


main()