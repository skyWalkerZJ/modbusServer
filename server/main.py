import socket
import light
import RPi.GPIO as GPIO
import dht11
import time
#位变量(1 bits)
discretesInput=[0]*10 #只读
coils=[0]*10 #读写
lights=[4,18,21,12,12,12,12,12,12,12]
#寄存器(16 bits)
inputRegisters=[0,0]*20 #只读
holdingRegisters=[0,0]*20 #读写
def updateRegister():
    #默认使用BCM26采集数据
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    instance=dht11.DHT11(26) #可修改BCM口
    result=instance.read()
    if result.is_valid():
        print("Temp: %d C" % result.temperature + ' ' + "Humid: %d %%" % result.humidity)
        inputRegisters[0]=result.temperature
        inputRegisters[1]=0 #温度小数部分
        holdingRegisters[0]=result.temperature
        holdingRegisters[1]=0 #温度小数部分
        inputRegisters[2]=result.humidity
        inputRegisters[3]=0 #湿度小数部分
        holdingRegisters[2]=result.humidity
        holdingRegisters[3]=0 #湿度小数部分
    else:
        print('数据采集失败')
def dealPdu(pdu):
    returnPDU=bytearray() #构造pdu返回值
    print(pdu)
    print(type(pdu))
    for i in range(0,4):
        returnPDU.append(pdu[i])#序列号和协议标识保持不变
    pdulength=pdu[4]*256+pdu[5]
    #此处需要插入两个字节的长度
    returnPDU.append(pdu[6])#单元标识符
    #报文头到此结束
    funCode=pdu[7]
    returnPDU.append(funCode)
    if funCode==0x01:#读线圈状态	读位（读N个bit）---读从机线圈寄存器，位操作
        beginPos=pdu[8]*256+pdu[9]
        readSize=pdu[10]*256+pdu[11]
        print("读取线圈状态 起始地址为",beginPos,"读取",readSize,"个bits")
        returnPDU.append(readSize%8+1)#数据所需字节数
        data=0
        flag=1
        for i in range(0,readSize):
            data+=coils[i+beginPos]*flag
            flag=flag*2
        data=data.to_bytes(readSize%8+1,'big')
        returnPDU.extend(data)
        returnPduLength=1+1+readSize%8+1+readSize%8+1
        returnPduLength=returnPduLength.to_bytes(2,'big')
        returnPDU.insert(4,returnPduLength[0])
        returnPDU.insert(5,returnPduLength[1])
    elif funCode==0x02:#读输入离散量	读位（读N个bit）---读离散输入寄存器，位操作
        beginPos = pdu[8] * 256 + pdu[9]
        readSize = pdu[10] * 256 + pdu[11]
        print("读取输入离散量状态 起始地址为", beginPos, "读取", readSize, "个bits")
        returnPDU.append(readSize % 8 + 1)  # 数据所需字节数
        data = 0
        flag = 1
        for i in range(0, readSize):
            data += discretesInput[i + beginPos] * flag
            flag = flag * 2
        data = data.to_bytes(readSize % 8 + 1, 'big')
        returnPDU.extend(data)
        returnPduLength = 1 + 1 + readSize % 8 + 1 + readSize % 8 + 1
        returnPduLength = returnPduLength.to_bytes(2, 'big')
        returnPDU.insert(4, returnPduLength[0])
        returnPDU.insert(5, returnPduLength[1])
    elif funCode==0x05:#写单个线圈	写位（写一个bit）---写线圈寄存器，位操作(FF 00为ON;00 00为OFF)
        beginPos = pdu[8] * 256 + pdu[9]
        state = ''
        if pdu[10]==0xFF:
            state='ON'
            coils[beginPos]=1
            #点亮线圈对应的led二极管
            light.light_ON(lights[beginPos])
        else:
            state='OFF'
            coils[beginPos]=0
            #熄灭线圈对应的led二极管
            light.light_OFF(lights[beginPos])
        print("置地址为", beginPos, "的线圈为",state)
        returnPDU.append(pdu[8])
        returnPDU.append(pdu[9])
        returnPDU.append(pdu[10])
        returnPDU.append(pdu[11])
        returnPDU.insert(4,pdu[4])
        returnPDU.insert(5,pdu[5])
    elif funCode==0x0F:#写多个线圈	可以写多个线圈---强置一串连续逻辑线圈的通断
        beginPos = pdu[8] * 256 + pdu[9]
        writeSize = pdu[10] * 256 + pdu[11]#写writeSize个bit
        print("写多个线圈 起始地址为", beginPos, "写", writeSize, "个bit")
        returnPDU.append(pdu[8])  # 起始地址
        returnPDU.append(pdu[9])  # 起始地址
        returnPDU.append(pdu[10])  # 写入bit数
        returnPDU.append(pdu[11])  # 写入bit数
        writeBytes = pdu[12]  # 写入字节数
        data = 0
        flag = 256 **(writeBytes-1)
        for i in range(0,writeBytes):
            data+=(pdu[13+i]*flag)
            flag=flag/256
        for i in range(0,writeSize):
            currentBit=data%2
            coils[beginPos+i]=currentBit
            if currentBit==1:# 点亮led灯
                light.light_ON(lights[beginPos+i])
            else:
                light.light_OFF(lights[beginPos+i])
            data=data>>1
        returnPDU.insert(4,0)  # 写多个线圈 头部长度固定 单元符(1)+功能码(1)+起始地址(2)+数据(2)
        returnPDU.insert(5,6)  # 固定长度为6
    elif funCode==0x03:#读多个寄存器	读整型、字符型、状态字、浮点型（读N个words）---读保持寄存器，字节操作
        updateRegister()
        beginPos = pdu[8] * 256 + pdu[9]
        readSize = pdu[10] * 256 + pdu[11]
        print("读取保持寄存器状态 起始地址为", beginPos, "读取", readSize, "个word")
        returnPDU.append(readSize * 2)
        for i in range(0, readSize):
            returnPDU.append(holdingRegisters[(beginPos + i) * 2])
            returnPDU.append(holdingRegisters[(beginPos + i) * 2 + 1])
        returnLength = 1 + 1 + 1 + readSize * 2
        returnLength = returnLength.to_bytes(2, 'big')
        returnPDU.insert(4, returnLength[0])
        returnPDU.insert(5, returnLength[1])
    elif funCode==0x04:#读输入寄存器	读整型、状态字、浮点型（读N个words）---读输入寄存器，字节操作
        updateRegister()
        beginPos = pdu[8] * 256 + pdu[9]
        readSize = pdu[10] * 256 + pdu[11]
        print("读取保持寄存器状态 起始地址为", beginPos, "读取", readSize, "个word")
        returnPDU.append(readSize * 2)  # 字节数
        for i in range(0, readSize):
            returnPDU.append(holdingRegisters[(beginPos + i) * 2])
            returnPDU.append(holdingRegisters[(beginPos + i) * 2 + 1])
        returnLength = 1 + 1 + 1 + readSize * 2
        returnLength = returnLength.to_bytes(2, 'big')
        returnPDU.insert(4, returnLength[0])
        returnPDU.insert(5, returnLength[1])
    elif funCode==0x10:#写多个保持寄存器	写多个保持寄存器---把具体的二进制值装入一串连续的保持寄存器
        print()
    elif funCode==0x06:#写单个保持寄存器	写整型、字符型、状态字、浮点型（写一个word）---写保持寄存器，字节操作
        print()
    return returnPDU
def main():
    s=socket.socket()
    hostname="192.168.43.184"
    port=502
    s.bind((hostname,port))
    s.listen(10)
    while True:
        sock, sock_addr = s.accept()  # 建立客户端连接
        print('连接地址：', sock_addr)
        data = sock.recv(1024)
        pdu = bytes(data)
        returnPDU = dealPdu (pdu)
        sock.send(bytes(returnPDU))
        sock.close()
if __name__=="__main__":
    main()
