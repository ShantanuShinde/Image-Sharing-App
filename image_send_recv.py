import numpy as np
import socket

# get checksum
def ones_complement(b):
    
    comp = format(int('FFFF', 16) - int(b, 16), 'x')
    return '0'*(4-len(comp)) + comp

def get_checksum(data):
    try:
        bin_data = ''.join([format(b, 'x') for b in data ])
    except:
        print(type(data))
    sum = '0000'
    for i in range(0, len(bin_data), 4):
            b = bin_data[i:i+4]
            sum = format(int(sum, 16) + int(ones_complement(b), 16), 'x')
            if len(sum) > 4:
                sum = format(int(sum[1:], 16) + 1, 'x')
    a = ones_complement(sum)
    return a


def recieve_image(recv_socket):
    img_shape = (200,200,4)
    dt = np.dtype('uint8')
    LRF = 0
    LAF = 1
    RWS = 1
    SEQ_NUM_TO_ACK = 1
    #MAX_SEQ_NUM = int(recv_socket.recv(4).decode())
    img_str = b""
    i = 0
    l = 0
    while True:
        if True:# (LAF > LRF and LAF - LRF <= RWS) or (LAF < LRF and  MAX_SEQ_NUM-LRF+LAF<=RWS):
            # receive frame
            frame = recv_socket.recv(107)

            #if len(frame) < 107:
            #    print(i,frame,len(frame))
            i +=1
            # check if frame is a over message
            l += len(frame)
            if frame[:4] == b'Over':
                break
            recv_socket.send('ack'.encode())
            # check if the sequence number is within windows, else discard the frame
            #seq_num = int(frame[:3].decode())
            if  True:#(seq_num > LRF or (LRF > LAF and seq_num > MAX_SEQ_NUM-LRF)) and (seq_num <= LAF or (LRF > LAF and seq_num <= (LAF+MAX_SEQ_NUM-LRF))):
                # check if the checksum is correct
                data = frame
                #chksm = get_checksum(data)
                if True: #chksm == frame[-4:].decode():
                    img_str+=data
                    # check if sequence num equal to SeqNumToAck
                    #if True:#int(frame[:3].decode()) == SEQ_NUM_TO_ACK:
                        # update LRF and LAF
                        #LRF = SEQ_NUM_TO_ACK
                        #LAF = (LRF + RWS)%(MAX_SEQ_NUM+1)
                        #if LAF == 0:
                        #    LAF+=1
                        # send acknowledgement
                    #    recv_socket.send(str(SEQ_NUM_TO_ACK).encode())
                    #SEQ_NUM_TO_ACK = (SEQ_NUM_TO_ACK+1)%(MAX_SEQ_NUM+1)
                    #if SEQ_NUM_TO_ACK == 0:
                    #    SEQ_NUM_TO_ACK+=1
    temp_arr = np.frombuffer(img_str, dtype=dt)
    return temp_arr.reshape(img_shape)

def receive_multiple_img(recv_socket):
    num = int(recv_socket.recv(3).decode())
    imgs = {}
    for i in range(num):
        #len_name = int(recv_socket.recv(2).decode())
        img_name = recv_socket.recv(10).decode()
        #print(img_name)
        recv_socket.send(b'a')
        imgs[img_name] = recieve_image(recv_socket)
    
    return imgs

def send_img(send_socket,img):
    img = img.flatten()
    
    img_str = img.tostring()
   
    SWS = 10
    LAR = 0
    LFS = 1
    FRAME_DATA_SIZE = 100
    SQ_NO_SIZE = 3
    MAX_SEQ_NUM = SWS+1
    #send_socket.send(str(MAX_SEQ_NUM).encode())
    j = 0
    if len(img_str) <= FRAME_DATA_SIZE:
        last = 1
    else:
        last = len(img_str)
    l = 0
    for i in range(0,last,FRAME_DATA_SIZE):
        
        # check if not window full
        if True:#(LFS > LAR and LFS-LAR <= SWS) or (LFS < LAR and MAX_SEQ_NUM-LAR+LFS<=SWS):

            data = img_str[i:i+FRAME_DATA_SIZE]
            l += len(data)
            
            # add sequence number and checksum 
            #lfs_str = str(LFS)
            #lfs_str = '0'*(SQ_NO_SIZE-len(lfs_str)) + lfs_str
            
            #checksum = get_checksum(data)
            #data = lfs_str.encode() + data + checksum.encode()

            send_socket.send(data)
            ack = send_socket.recv(3)
            #lfs = (LFS+1)%(MAX_SEQ_NUM+1)
            #if lfs==0:
            #    lfs+=1
            #ack = send_socket.recv(1)
            #ack = ack.decode()
            #LAR = int(ack)
           
                     
    # send over message and close the socket
    send_socket.send('Over'.encode())
    
def send_multiple_imgs(send_socket, imgs):
    num = str(len(imgs))
    send_socket.send(('0'*(3-len(num)) + num).encode())
    for img in imgs:
        #len_name = str(len(img))
        #send_socket.send(('0'*(2-len(len_name)) + len_name).encode())
        send_socket.send(img.encode())
        send_socket.recv(1)
        #print("here1")
        send_img(send_socket,imgs[img])
    