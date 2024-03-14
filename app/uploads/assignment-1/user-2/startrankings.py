from PIL import Image
from tkinter import *
from tkinter import ttk
from tkinter import *  
from PIL import ImageTk,Image  
import os


def displayPosters():
	win= Tk()

	w = 800 # width for the Tk root
	h = 300 # height for the Tk root

	def rank3():
		os.system('python ranknewest.py')
	ws = win.winfo_screenwidth() # width of the screen
	hs = win.winfo_screenheight() # height of the screen

	def rank1():
		os.system('python rankings.py')
	x = (ws/2)
	y = (hs/2) - (h/2)
	def rank2():
		os.system('python rankingscentered.py')
    
	win.geometry('%dx%d+%d+%d' % (w, h, x, y))

	# win.geometry('800x750'
	win.title('Movie Rankings')
	Label(win, text= "What would you like to do ?", font= ('Aerial 17 bold italic')).pack(pady= 30)

	top = Frame(win)
	bottom = Frame(win)
	top.pack(side=TOP)
	bottom.pack(side=BOTTOM)
	lists = Frame(win)
	lists.pack(in_=top, side=BOTTOM)
    

	ttk.Button(win, text='Random Ranking', command=rank1).pack(in_=top, side=LEFT)
	ttk.Button(win, text= 'Fullscreen Random Ranking', command=rank2).pack(in_=top, side=LEFT)
	ttk.Button(win, text= 'Rank Newest', command=rank3).pack(in_=top, side=LEFT)
	
	win.mainloop()


displayPosters()

