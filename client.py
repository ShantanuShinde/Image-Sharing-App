import socket
import numpy as np
from PIL import Image as Img, ImageTk
from tkinter import *
from tkinter import font
from image_send_recv import receive_multiple_img, recieve_image, send_img
from tkinter.filedialog import askopenfilename
import re

class ImageShareApp(Tk):
    def __init__(self, *args, **kwargs):
        # call the parent constructor
        Tk.__init__(self, *args, **kwargs)
        # set title text and font
        self.title("Image Share App")
        self.title_font = font.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        # connect to the server
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.socket.connect((socket.gethostname(), 8080))
        # initialize the main frame
        container = Frame(self,width=500, height=500)
        container.pack(side="top",fill="both",expand="true")
        container.pack_propagate(0)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # initialize frames
        self.frames = {}
        for f in (StartPage, LoginPage, RegisterPage, DeletePage):
            page_name = f.__name__
            frame = f(parent = container, controller = self)
            self.frames[page_name] = frame
            frame.grid(row = 0, column = 0, sticky = "nsew")

        self.show_frame("StartPage")
    def show_frame(self, page_name,send_msg=True):
        ''' Show frame of the name passed'''
        if send_msg:
            self.socket.send(page_name[:-4].lower().encode())
        frame = self.frames[page_name]
        frame.tkraise()

class StartPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent,width=500,height=500)
        parent.grid_propagate(0)
        self.grid_propagate(0)
        self.controller = controller
        label = Label(self, text = "Welcome to the Image Sharing App", font = controller.title_font)
        label.place(relx = .5, rely = 0.2, anchor="center")
        

        button1 = Button(self, text = "Login", command = lambda:controller.show_frame("LoginPage"),height=2,width=11)
        button2 = Button(self, text = "Register", command = lambda:controller.show_frame("RegisterPage"),height=2,width=11)
        button3 = Button(self, text = "Delete Account", command = lambda:controller.show_frame("DeletePage"),height=2,width=11)

        button1.place(relx=.5,rely=.5,anchor="center")
        button2.place(relx=.5,rely=.6,anchor="center")
        button3.place(relx=.5,rely=.7,anchor="center")

class LoginPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self,parent,width=500,height=500)
        parent.grid_propagate(0)
        self.controller = controller
        label1 = Label(self, text = "Login", font = controller.title_font)
        label1.place(relx = .5, rely = 0.2, anchor="center")
        label2 = Label(self,text="Enter user id:")
        label2.place(relx=.5,rely=.4,anchor="center")
        label3 = Label(self,text="Enter password:")
        label3.place(relx=.5,rely=.5,anchor="center")
        en1 = Entry(self)
        en2 = Entry(self,show="*")
        en1.place(relx=.5,rely=.45,anchor="center")
        en2.place(relx=.5,rely=.55,anchor="center")
        button1 = Button(self,text="Login",height=2,width=11,command=lambda:self.login(parent,en1,en2))
        button2 = Button(self, text="Back", command = lambda:[en1.delete(0,'end'), en2.delete(0,'end'),controller.show_frame("StartPage")],height=2,width=11)
        button1.place(relx=.5,rely=.65,anchor="center")
        button2.place(relx=.5,rely=.75,anchor="center")

    def invalid_popup(self):
        win = Toplevel()
        win.wm_title("Error")
        l = Label(win, text="Invalid user id or password!")
        l.grid(row=0, column=0)
        b = Button(win, text="Okay", command=win.destroy)
        b.grid(row=1, column=0)

    def login(self, parent, en1, en2):
        id = en1.get()
        pas = en2.get()
        en1.delete(0,'end')
        en2.delete(0,'end')
        if not id.isdigit() or len(pas) > 12 or len(pas) == 0 or len(id) == 0 or len(id) > 10:
            self.invalid_popup()
        else:
            self.controller.socket.send(id.encode())
            self.controller.socket.recv(1)
            self.controller.socket.send(pas.encode())
            ack = self.controller.socket.recv(40).decode()
            if ack[:3] == "Inc":
                self.invalid_popup()
            else:
                account_name = ack[3:]
                acnt = Account(parent,self.controller,account_name)
                acnt.grid(row = 0, column = 0, sticky = "nsew")
                acnt.tkraise()

            
class Account(Frame):
    def __init__(self, parent, controller, account_name):
        Frame.__init__(self,parent,width=500,height=500)
        parent.grid_propagate(0)
        self.controller = controller
        imgs_exist = self.controller.socket.recv(3).decode()
        self.controller.socket.send(b'a')
        img_panel = Label(self)#, image=self.cur_img)
        img_panel.place(relx = .5, rely=.45, anchor='center')
        if imgs_exist == 'non':
            self.imgs = {}
            self.img_names = []
            self.end = 0
            self.cur = 0
        else:
            self.imgs = receive_multiple_img(self.controller.socket)
            self.img_names = list(self.imgs.keys())
            self.cur = 0
            self.end = len(self.img_names)-1
            
            self.cur_img = ImageTk.PhotoImage(Img.fromarray(self.imgs[self.img_names[self.cur]]).resize((300,300)))
            img_panel.configure(image=self.cur_img)
            #img_panel.image = self.cur_img 


        label1 = Label(self, text = account_name, font = controller.title_font)
        label1.place(relx = .5, rely = 0.05, anchor="center")    
        
        label2 = Label(self,text="Enter user id to send to:",font=font.Font(family='Helvetica', size=10))
        e1 = Entry(self)
        
        label2.place(relx=0.8, rely=0.8,anchor="center")
        e1.place(relx=0.8,rely=0.85,anchor="center")
        label3 = Label(self,text='Enter image name')
        e2 = Entry(self)
        b5 = Button(self, text="Upload\nImage",height=2,width=7, command=lambda:self.upload(e2,img_panel))
        label3.place(relx=.5,rely=.8,anchor='center')
        e2.place(relx=.5,rely=.85,anchor='center')
        if len(self.img_names) == 0:
            name = ''
        else:
            name = self.img_names[self.cur]
        label4 = Label(self,text=name)
        label4.place(relx=.5,rely=.12,anchor="center")
        b1 = Button(self,text="<",height=3,width=2,font=font.Font(family='Helvetica', size=18),command=lambda:self.go_left(img_panel,label4))
        b2 = Button(self,text=">",height=3,width=2,font=font.Font(family='Helvetica', size=18),command=lambda:self.go_right(img_panel,label4))
        b3 = Button(self,text="Logout",height=2,width=5,command=lambda:self.logout())
        b1.place(relx=.12, rely=.5,anchor="center")
        b2.place(relx=.88,rely=.5,anchor="center")
        b3.place(relx = .9, rely=.2,anchor="center")
        b4 = Button(self,text="Send",height=1,width=5,command=lambda:self.send(e1))
        b4.place(relx=0.8,rely=0.91,anchor="center")
        b5 = Button(self, text="Upload\nImage",height=2,width=7, command=lambda:self.upload(e2,img_panel))
        b5.place(relx = 0.5,rely=0.92,anchor="center")
        b6 = Button(self, text="Delete", height=1, width=5, command=lambda:self.delete(img_panel,label4))
        b6.place(relx=.12, rely=.8, anchor='center')


    def upload(self, e2,img_panel):
        name = e2.get()
        if len(name)>10:
            self.invalid_popup("Image name must be less than 10 characters!")
        elif not re.match("^[A-Za-z0-9_-]*$", name):
            self.invalid_popup("Image name can only have alphanumbes, _ and -")
        else:
            self.controller.socket.send('upload'.encode())
            self.controller.socket.send(name.encode())
            ack = self.controller.socket.recv(10).decode()
            if ack == 'nonunique':
                self.invalid_popup('Image name already used!')
            else:
                path = askopenfilename(filetypes=[("Image File",".jpg"),("Image File",".png")])
                img = Img.open(path)
                img = img.resize((200,200))
                img_arr = np.array(img)
                if len(self.imgs) < 6:
                    self.imgs[name] = img_arr
                    self.img_names.append(name)
                    self.end = len(self.img_names) - 1
                    if len(self.imgs) == 1:
                        self.cur_img = ImageTk.PhotoImage(img)
                        img_panel.configure(image=self.cur_img)
                        #img_panel.image = self.cur_img
                send_img(self.controller.socket, img_arr)    

    def go_left(self,img_panel,label):
        if self.cur != 0:
            self.cur -= 1
            self.cur_img = ImageTk.PhotoImage(Img.fromarray(self.imgs[self.img_names[self.cur]]).resize((300,300)))
            img_panel.configure(image = self.cur_img)
            label.configure(text=self.img_names[self.cur])
            label.text = self.img_names[self.cur]
        else:
            self.controller.socket.send('left_img'.encode())
            ack = self.controller.socket.recv(2).decode()
            if ack != 'no':
                name = self.controller.socket.recv(10).decode()
                self.controller.socket.send(b'ac')
                img = recieve_image(self.controller.socket)
                self.cur_img = ImageTk.PhotoImage(Img.fromarray(img).resize((300,300)))
                self.img_names.insert(0,name)
                self.imgs[name] = img
                img_panel.configure(image = self.cur_img)
                label.configure(text=self.img_names[self.cur])
                label.text = self.img_names[self.cur]
                if len(self.img_names) > 6:
                    del self.imgs[self.img_names[-1]]
                    self.img_names.pop()


    
    def go_right(self,img_panel,label):
        if self.cur < self.end:
            self.cur+=1
            self.cur_img = ImageTk.PhotoImage(Img.fromarray(self.imgs[self.img_names[self.cur]]).resize((300,300)))
            img_panel.configure(image = self.cur_img)
            #img_panel.image = self.cur_img
            label.configure(text=self.img_names[self.cur])
            label.text = self.img_names[self.cur]
        else:
            self.controller.socket.send('right_img'.encode())
            ack = self.controller.socket.recv(2).decode()
            if ack != 'no':
                name = self.controller.socket.recv(10).decode()
                self.controller.socket.send(b'ac')
                img = recieve_image(self.controller.socket)
                self.img_names.append(name)
                self.imgs[name] = img
                self.cur_img = ImageTk.PhotoImage(Img.fromarray(img).resize((300,300)))
                img_panel.configure(image = self.cur_img)
                #img_panel.image = self.cur_img
                label.configure(text=self.img_names[self.cur])
                label.text = self.img_names[self.cur]
                if len(self.img_names) > 6:
                    del self.imgs[self.img_names[0]]
                    self.img_names.pop(0)
                else:
                    self.end +=1

    def invalid_popup(self, text):
        win = Toplevel()
        win.wm_title("Error")
        l = Label(win, text=text)
        l.grid(row=0, column=0)
        b = Button(win, text="Okay", command=win.destroy)
        b.grid(row=1, column=0)

    def logout(self):
        self.controller.socket.send("logout".encode())
        self.controller.show_frame("StartPage",False)

    def send(self, en1):
        self.controller.socket.send('send'.encode())
        usr_id = en1.get()
        self.controller.socket.send(usr_id.encode())
        ack = self.controller.socket.recv(4).decode()
        if ack == "inc":
            self.invalid_popup("Invalid user id or password!")
        else:
            en1.delete(0,'end')
            self.controller.socket.send(self.img_names[self.cur].encode())

    def delete(self,img_panel, label4):
        self.controller.socket.send('delete'.encode())
        self.controller.socket.send(self.img_names[self.cur].encode())
        del self.imgs[self.img_names[self.cur]]
        self.img_names.pop(self.cur)
        if len(self.img_names) == 1:
            img_panel.configure(image='')
            label4.configure(text = '')
        elif self.cur == self.end:
            self.cur-=1
            self.cur_img = ImageTk.PhotoImage(Img.fromarray(self.imgs[self.img_names[self.cur]]).resize((300,300)))
            img_panel.configure(image = self.cur_img)
            label4.configure(text = self.img_names[self.cur])
        else:
            self.cur+=1
            self.cur_img = ImageTk.PhotoImage(Img.fromarray(self.imgs[self.img_names[self.cur]]).resize((300,300)))
            img_panel.configure(image = self.cur_img) 
            label4.configure(text = self.img_names[self.cur])
        self.end = len(self.img_names)-1

class RegisterPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self,parent,width=500,height=500)
        parent.grid_propagate(0)
        self.controller = controller
        label = Label(self, text = "Register", font = controller.title_font)
        label.place(relx = .5, rely = 0.2, anchor="center")
        l1 = Label(self,text="Enter user id:")
        l2 = Label(self,text="Enter user name:")
        l3 = Label(self, text="Enter password")
        l1.place(relx=.5,rely=.35,anchor="center")
        l2.place(relx=.5,rely=.45,anchor="center")
        l3.place(relx=.5,rely=.55,anchor="center")
        en1 = Entry(self, textvariable=StringVar(self))
        en2 = Entry(self, textvariable=StringVar(self))
        en3 = Entry(self,show="*",textvariable=StringVar(self))
        en1.place(relx=.5,rely=0.4,anchor="center")
        en2.place(relx=.5,rely=0.5,anchor="center")
        en3.place(relx=.5,rely=.6,anchor="center")
        button1 = Button(self,text="Register",height=2,width=11,command=lambda:self.register(parent,en1,en2,en3))
        button2 = Button(self, text="Back", command = lambda:controller.show_frame("StartPage"),height=2,width=11)
        button1.place(relx=.5,rely=.7,anchor="center")
        button2.place(relx=.5,rely=.8,anchor="center")
        self.bind("<Return>",lambda:self.register(parent,en1,en2))


    def popup(self, msg):
        win = Toplevel()
        win.wm_title("Error")
        l = Label(win, text=msg)
        l.grid(row=0, column=0)
        b = Button(win, text="Okay", command=win.destroy)
        b.grid(row=1, column=0)

    def register(self, parent,en1,en2,en3):
        ack = self.controller.socket.recv(6).decode()
        if ack == "max":
            self.popup("User limit reached")
            self.controller.show_frame("StartPage",False)
        id = en1.get()
        name = en2.get()
        pas = en3.get()
        en1.delete(0,'end')
        en2.delete(0,'end')
        en3.delete(0,'end')
        if not id.isdigit() or len(pas) > 12 or len(pas) == 0 or len(id) == 0 or len(id) > 10:
            self.popup("Invalid user id or password!")
        else:
            self.controller.socket.send(id.encode())
            ack = self.controller.socket.recv(3).decode()
            if ack == "dup":
                self.popup("User Id already used!")
            else:
                self.controller.socket.send(name.encode())
                self.controller.socket.send(pas.encode())
                self.popup("Account created successfully")
                self.controller.show_frame("StartPage",False)
    
    
            

class DeletePage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self,parent,width=500,height=500)
        parent.grid_propagate(0)
        self.controller = controller
        label = Label(self, text = "Delete", font = controller.title_font)
        label.place(relx = .5, rely = 0.2, anchor="center")
        l1 = Label(self, text = "Enter user id:")
        l2 = Label(self, text="Enter password:")
        l1.place(relx=.5, rely=.55,anchor="center")
        l2.place(relx=.5, rely=.65,anchor="center")
        en1 = Entry(self, textvariable=StringVar(self))
        en2 = Entry(self,show="*",textvariable=StringVar(self))
        en1.place(relx=.5,rely=0.4,anchor="center")
        en2.place(relx=.5,rely=0.45,anchor="center")
       
        button1 = Button(self,text="Delete",height=2,width=11,command=lambda:self.delete_acnt(parent,en1,en2))
        button2 = Button(self, text="Back", command = lambda:controller.show_frame("StartPage"),height=2,width=11)
        button1.place(relx=.5,rely=.6,anchor="center")
        button2.place(relx=.5,rely=.7,anchor="center")

        self.bind("<Return>",lambda:self.delete_acnt(parent,en1,en2))

    def popup(self, msg):
        win = Toplevel()
        win.wm_title("Error")
        l = Label(win, text=msg)
        l.grid(row=0, column=0)
        b = Button(win, text="Okay", command=win.destroy)
        b.grid(row=1, column=0)

    def delete_acnt(self, parent,en1,en2):
        id = en1.get()
        pas = en2.get()
        if not id.isdigit() or len(pas) > 12 or len(pas) == 0 or len(id) == 0 or len(id) > 10:
            self.popup("Invalid user id or password!")
        else:
            self.controller.socket.send(id.encode())
            self.controller.socket.send(pas.encode())
            ack = self.controller.socket.recv(3).decode()
            if ack == "inc":
                self.popup("Invalid user id or password!")
            else:
                self.popup("Account deleted successfully")
                self.controller.show_frame("StartPage",False)



       
if __name__ == "__main__":
    app = ImageShareApp()
    app.mainloop()