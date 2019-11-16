import socket
import _thread as thread
from PIL import Image
import numpy as np 
import os
import sqlite3
import shutil
from image_send_recv import recieve_image, send_multiple_imgs, send_img
import re

conn = sqlite3.connect('database/ISA.db')
cr = conn.cursor()

REG_MAX = 10

cr.execute('CREATE TABLE IF NOT EXISTS USERS(user_id INTEGER PRIMARY KEY, user_name VARCHAR(30), password VARCHAR(12))')
cr.execute('CREATE TABLE IF NOT EXISTS PICTURES(pic_name VARCHAR(20), user_id INTEGER , pic_path VARCHAR(100), PRIMARY KEY(pic_name, user_id), FOREIGN KEY(user_id) REFERENCES users(user_id))')
conn.commit()
IMAGE_PATH = 'database/images/'

def on_new_client(clientsocket,addr):
    conn = sqlite3.connect('database/ISA.db')
    cur = conn.cursor()
    while True:
        act = clientsocket.recv(10).decode()
        
        if act == 'login':
            
            while True:
                msg = clientsocket.recv(10).decode()
                
                if msg == 'start':
                    break
                else:
                    id = int(msg)
                    clientsocket.send(b'a')
                pas = clientsocket.recv(12).decode()

                cur.execute("Select password from users where user_id = " + msg)
                p = cur.fetchall()
                if len(p) == 0 or p[0][0] != pas:
                    clientsocket.send('Inc'.encode())
                else:
                    cur.execute("select user_name from users where user_id = " + str(id))
                    un = cur.fetchall()[0][0]
                    clientsocket.send(('Cor' + un).encode())
                    cur.execute("select pic_name,pic_path from pictures where user_id = " + str(id))
                    
                    im = cur.fetchall()
                    
                    if len(im) == 0:
                        clientsocket.send('non'.encode())
                        clientsocket.recv(1)
                    else:
                        if len(im) > 6:
                            im = im[:6]
                        clientsocket.send('yes'.encode())
                        clientsocket.recv(1)
                        imgs = {}
                        for i in im:
                            imgs[i[0]] = np.array(Image.open(i[1]))
                        send_multiple_imgs(clientsocket,imgs)
                    left = 0
                    right = len(im)-1
                    while True:
                        
                        act1 = clientsocket.recv(10).decode()
                        if act1 =='upload':
                            while True:
                                name = clientsocket.recv(10).decode()
                                cur.execute("select * from pictures where pic_name = '" + name + "' and user_id = " + str(id))
                                p = cur.fetchall()
                                if len(p) == 0:
                                    clientsocket.send('unique'.encode())
                                    img = Image.fromarray(recieve_image(clientsocket))
                                    path = IMAGE_PATH + str(id)+'/' + name
                                    img.save(path,'png')
                                    cur.execute('insert into pictures values(?,?,?)',(name, id, path))
                                    conn.commit()
                                    #cur.execute("select all_images from user_image where user_id = " + str(id) )
                                    #p = cur.fetchall()
                                    #if len(p) == 0:
                                    #    cur.execute('insert into all_images values (?,?)',(id,name))
                                    #else:
                                    #    names = p[0][0]
                                    #    names += ',' + name
                                    #    cur.execute("update user_image set all_images = '" + names + "' where user_id = " + str(id))
                                    #conn.commit()
                                    break
                                else:
                                    clientsocket.send('nonunique'.encode())
                        elif act1 == 'send':
                            while True:
                                print("here")
                                usr = clientsocket.recv(10).decode()
                                cur.execute("select * from users where user_id = " + usr )
                                p = cur.fetchall()
                                if len(p) != 0:
                                    p = cur.fetchall()
                                    clientsocket.send(('cor ').encode())
                                    img_name = clientsocket.recv(10).decode()
                                    cur.execute("select * from pictures where user_id = " + usr + " and pic_name = '" + img_name + "'")
                                    p = cur.fetchall()
                                    print(p)
                                    if len(p) >0:
                                        cur.execute("select pic_name from pictures where user_id = " + usr + " and pic_name like '" + img_name + "(%)' order by pic_name desc")
                                        p = cur.fetchall()
                                        if len(p) > 0:
                                            n = int(re.findall("\(([^[\]]*)\)", p[0][0])[0])
                                        else:
                                            n = 0
                                        im_name = img_name + "(" + str(n+1) + ")"
                                    else:
                                        im_name = img_name
                                    cur.execute("select pic_path from pictures where user_id = " + str(id) + " and pic_name = '" + img_name + "'")
                                    p = cur.fetchall()
                                    print(p)
                                    new_path = IMAGE_PATH + usr + "/" + im_name
                                    shutil.copy2(p[0][0],IMAGE_PATH + usr + "/" + im_name)
                                    cur.execute("insert into pictures values (?,?,?)",(im_name,usr,new_path))
                                    conn.commit()
                                    
                                    break
                                else:
                                    clientsocket.send('inc'.encode())
                        elif act1 == 'left_img':
                            if left>0:
                                clientsocket.send('ye'.encode())
                                cur.execute("select pic_name,pic_path from pictures where user_id = " + str(id))
                                im = cur.fetchall()
                                left-=1
                                if right-left > 5:
                                    right-=1
                                napa = im[left]
                                clientsocket.send(napa[0].encode())
                                clientsocket.recv(2)
                                send_img(clientsocket,np.array(Image.open(napa[1])))
                            else:
                                clientsocket.send('no'.encode())
                        elif act1 == 'right_img':
                            cur.execute("select pic_name,pic_path from pictures where user_id = " + str(id))
                            im = cur.fetchall()
                            if len(im)-1 > right:
                                clientsocket.send('ye'.encode())
                                right+=1
                                if right-left > 5:
                                    left+=1
                                napa = im[right]
                                clientsocket.send(napa[0].encode())
                                clientsocket.recv(2)
                                send_img(clientsocket,np.array(Image.open(napa[1])))
                            else:
                                clientsocket.send('no'.encode())
                        elif act1 == 'delete':
                            name = clientsocket.recv(10).decode()
                            cur.execute("select pic_path from pictures where user_id = " + str(id)  + " and pic_name = '" + name + "'")
                            p = cur.fetchall()
                            os.remove(p[0][0])
                            cur.execute("delete from pictures where user_id = " + str(id) + " and pic_name = '" + name +"'")
                            conn.commit()

                        elif act1 == 'logout':
                            break
                                
                    break
        elif act == 'register':
            cur.execute("select count(user_id) from users")
            p = cur.fetchall()
            if len(p) == REG_MAX:
                clientsocket.send('max'.encode())
            else:
                clientsocket.send('nomax'.encode())
                while True:
                    id = clientsocket.recv(10).decode()
                    if id == "start":
                        break
                    cur.execute("select * from users where user_id = " + id)
                    p = cur.fetchall()
                    if len(p) > 0:
                        clientsocket.send('dup'.encode())
                    else:
                        clientsocket.send('not'.encode())
                        name = clientsocket.recv(30).decode()
                        pas = clientsocket.recv(12).decode()
                        cur.execute("insert into users values (?,?,?)",(id,name,pas))
                        conn.commit()
                        os.makedirs(IMAGE_PATH + id)
                        break
        elif act == 'delete':
            while True:
                id = clientsocket.recv(10).decode()
                if id == "start":
                    break
                pas = clientsocket.recv(12).decode()
                cur.execute("select password from users where user_id = " + id)
                p = cur.fetchall()
                if len(p) == 0 and p[0][0] != pas:
                    clientsocket.send('inc'.encode())
                    continue
                clientsocket.send('cor'.encode())
                cur.execute('delete from users where user_id = ' + id)
                cur.execute("delete from pictures where user_id = " + id)
                #cur.execute("delete from user_image where user_id = " + id)
                conn.commit()
                shutil.rmtree(IMAGE_PATH + "/" + id)
                break
            
        elif act == 'close':
            break     
    clientsocket.close()

s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 8080                # Reserve a port for your service.

print('Server started!')
print ('Waiting for clients...')

s.bind((host, port))        # Bind to the port
s.listen(5)                 # Now wait for client connection.

while True:
   c, addr = s.accept()     # Establish connection with client.
   thread.start_new_thread(on_new_client,(c,addr))
   
s.close()