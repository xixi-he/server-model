# server-model

依次实现了：一个server如何并发处理多个请求的不同方式，也像是历史演进吧，从而加深理解

thread.py：一个连接创建一个线程去处理
thread_pool.py：还是一个连接一个线程，但是用线程池来限制线程总数和线程复用
select.py：单个线程，利用IO多路复用实现单个线程并发处理多个连接
thread_pool_select.py：多线程，每个线程内部使用IO多路复用处理多个线程的写法1
thread_pool_select_v2.py：多线程，每个线程内部使用IO多路复用处理多个线程的写法1
