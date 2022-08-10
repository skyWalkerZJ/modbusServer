import socket

s = socket.socket()  # 创建 socket 对象
host = '192.168.43.184'  # 获取本地主机名
#host='127.0.0.1'
port = 502  # 设置端口号

data=[0x00,0x01,0x00,0x00,0x00,0x06,0x01,0x04,0x00,0x00,0x00,0x02]
s.connect((host, port))
s.send(bytes(data))
recvData=s.recv(1024)
print(recvData.hex())
s.close()