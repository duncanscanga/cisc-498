import random
from PIL import Image
from tkinter import *
from tkinter import ttk
from tkinter import *  
from PIL import ImageTk,Image  
import math


def readMovies():
	# Using readlines()
	file1 = open('movies.txt', 'r')
	Lines = file1.readlines()
	
	movieCount = []
	movieCount.append(len(Lines))

	for row in range(movieCount[0]):
		movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
		data = Lines[row].split('\t')
		movie['title'] = data[0]
		movie['genre'] = data[1]
		movie['year'] = data[2]
		movie['poster'] = data[3]
		movie['points'] = int(data[4])
		movie['rewatch'] = int(data[5])
		movie['count'] = int(data[6])
		movies.append(movie)
	file1.close()

	return movieCount[0]

def getRandomMovie(movieCount):
	while True:
		indexes = []
		indexes.append(random.randint(0,movieCount[0] - 1))
		indexes.append(random.randint(0,movieCount[0] - 1))
		if indexes[0] != indexes[1]:
			break
	return indexes

def firstMovieChosen(indexes):
	index1 = indexes[0]
	index2 = indexes[1]
	Pb =  Probability(movies[index1]['points'], movies[index2]['points'])
	Pa =  Probability(movies[index2]['points'], movies[index1]['points'])
	Ra = int(movies[index1]['points'] + 50 * (1 - Pa))
	Rb = int(movies[index2]['points'] + 50 * (0 - Pb))

	file = open('movies.txt', 'r')
	orig = file.readlines()
	
	movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
	data = orig[index1].split('\t')
	movie['title'] = data[0]
	movie['genre'] = data[1]
	movie['year'] = data[2]
	movie['poster'] = data[3]
	movie['points'] = int(data[4])
	movie['rewatch'] = int(data[5])
	movie['count'] = int(data[6])
	
	update = movie['title'] + '\t' + movie['genre'] + '\t' + movie['year'] + '\t' + movie['poster'] + '\t' + str(Ra) + '\t' +  str(movie['rewatch']) + '\t' + str(movie['count'] + 1) + '\n'
	orig[index1] = update
	
	movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
	data = orig[index2].split('\t')
	movie['title'] = data[0]
	movie['genre'] = data[1]
	movie['year'] = data[2]
	movie['poster'] = data[3]
	movie['points'] = int(data[4])
	movie['rewatch'] = int(data[5])
	movie['count'] = int(data[6])
	
	update = movie['title'] + '\t' + movie['genre'] + '\t' + movie['year'] + '\t' + movie['poster'] + '\t' + str(Rb) + '\t' +  str(movie['rewatch']) + '\t' + str(movie['count'] + 1) + '\n'
	orig[index2] = update

	file.close()

	with open('movies.txt', 'w') as file2:
		file2.writelines( orig )
	
	file2.close()
	

def secondMovieChosen(indexes):
   index2 = indexes[1]
   index1 = indexes[0]
   Pb =  Probability(movies[index1]['points'], movies[index2]['points'])
   Pa =  Probability(movies[index2]['points'], movies[index1]['points'])
   Ra = int(movies[index1]['points'] + 30 * (0 - Pa))
   Rb = int(movies[index2]['points'] + 30 * (1 - Pb))
   
   
   file = open('movies.txt', 'r')
   orig = file.readlines()
   
   movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
   data = orig[index1].split('\t')
   movie['title'] = data[0]
   movie['genre'] = data[1]
   movie['year'] = data[2]
   movie['poster'] = data[3]
   movie['points'] = int(data[4])
   movie['rewatch'] = int(data[5])
   movie['count'] = int(data[6])
   
   update = movie['title'] + '\t' + movie['genre'] + '\t' + movie['year'] + '\t' + movie['poster'] + '\t' + str(Ra) + '\t' +  str(movie['rewatch']) + '\t' + str(movie['count'] + 1)  + '\n'
   orig[index1] = update

   movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
   data = orig[index2].split('\t')
   movie['title'] = data[0]
   movie['genre'] = data[1]
   movie['year'] = data[2]
   movie['poster'] = data[3]
   movie['points'] = int(data[4])
   movie['rewatch'] = int(data[5])
   movie['count'] = int(data[6])
   
   update = movie['title'] + '\t' + movie['genre'] + '\t' + movie['year'] + '\t' + movie['poster'] + '\t' + str(Rb) + '\t' +  str(movie['rewatch']) + '\t' + str(movie['count'] + 1) + '\n'
   orig[index2] = update


   file.close()
   with open('movies.txt', 'w') as file2: 
       file2.writelines( orig )
   file2.close()


def Probability(rating1, rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

def orderedList():
	file1 = open('movies.txt', 'r')
	Lines = file1.readlines()
	
	movieCount = []
	movieCount.append(len(Lines))
	movies = []
	
	for row in range(movieCount[0]):
		movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
		data = Lines[row].split('\t')
		movie['title'] = data[0]
		movie['genre'] = data[1]
		movie['year'] = data[2]
		movie['poster'] = data[3]
		movie['points'] = int(data[4])
		movie['rewatch'] = int(data[5])
		movie['count'] = int(data[6])
		movies.append(movie)
	file1.close()

	movies2 = sorted(movies, key=lambda item: item['points'], reverse=True)

	scores = Tk() 


	scores.title('List')
	label = ttk.Label(scores, text="Movie Scores", font=("Arial",30)).grid(row=0, columnspan=5)
	cols = ('Position', 'Title', 'Genre', 'Year', 'Count', 'Points')
	listBox = ttk.Treeview(scores, columns=cols, show='headings', height=50)
	for col in cols:
		listBox.heading(col, text=col)    
	listBox.grid(row=2, column=0, columnspan=6)

	movies3 = []
	for i in range(len(movies2)):
		movie = []
		movie.append(i + 1)
		movie.append(movies2[i]['title'])
		movie.append(movies2[i]['genre'])
		movie.append(movies2[i]['year'])
		movie.append(movies2[i]['count'])
		movie.append(movies2[i]['points'])
		movies3.append(movie)
		listBox.insert("", "end", values=(movie[0], movie[1], movie[2], movie[3], movie[4], movie[5]))

	for i in range(20):
		listBox.insert("", "end", values=("", "", "", "", "", ""))
	
	scores.mainloop()

def rewatch(index):
	file = open('movies.txt', 'r')
	orig = file.readlines()

	movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
	data = orig[index].split('\t')
	movie['title'] = data[0]
	movie['genre'] = data[1]
	movie['year'] = data[2]
	movie['poster'] = data[3]
	movie['points'] = int(data[4])
	movie['rewatch'] = int(data[5])
	movie['count'] = int(data[6])

	update = movie['title'] + '\t' + movie['genre'] + '\t' + movie['year'] + '\t' + movie['poster'] + '\t' + str(movie['points']) + '\t' +  str(1) + '\t' + str(movie['count']) + '\n'
	orig[index] = update

	file.close()

	with open('movies.txt', 'w') as file2:
		file2.writelines( orig )
	
	file2.close()

def unRewatch(index):
	file = open('movies.txt', 'r')
	orig = file.readlines()
	
	movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count': 0}
	data = orig[index].split('\t')
	movie['title'] = data[0]
	movie['genre'] = data[1]
	movie['year'] = data[2]
	movie['poster'] = data[3]
	movie['points'] = int(data[4])
	movie['rewatch'] = int(data[5])
	movie['count'] = int(data[6])

	update = movie['title'] + '\t' + movie['genre'] + '\t' + movie['year'] + '\t' + movie['poster'] + '\t' + str(movie['points']) + '\t' +  str(0) + '\t' + str(movie['count']) +  '\n'
	orig[index] = update

	file.close()

	with open('movies.txt', 'w') as file2:
		file2.writelines( orig )
	
	file2.close()


def moviesToRewatch():
	file1 = open('movies.txt', 'r')
	Lines = file1.readlines()
	
	movieCount = []
	movieCount.append(len(Lines))
	movies = []

	for row in range(movieCount[0]):
		movie = {'title': '', 'genre': 0, 'year': '', 'poster': '', 'points': 0, 'rewatch': 0, 'count' : 0}
		data = Lines[row].split('\t')
		movie['title'] = data[0]
		movie['genre'] = data[1]
		movie['year'] = data[2]
		movie['poster'] = data[3]
		movie['points'] = int(data[4])
		movie['rewatch'] = int(data[5])
		movie['count'] = int(data[6])
		movies.append(movie)
	file1.close()

	movies2 = sorted(movies, key=lambda item: item['points'], reverse=True)

	scores = Tk() 
	scores.title('Rewatch')
	label = ttk.Label(scores, text="Movies To Rewatch", font=("Arial",30)).grid(row=0, columnspan=3)
	cols = ('Position', 'Title', 'Genre', 'Year', 'Count', 'Points')
	listBox = ttk.Treeview(scores, columns=cols, show='headings', height=50)
	for col in cols:
		listBox.heading(col, text=col)    
	listBox.grid(row=1, column=0, columnspan=5)

	movies3 = []

	for i in range(len(movies)):
		if movies2[i]['rewatch'] == 1:	
			movie = []
			movie.append(movies2[i]['title'])
			movie.append(movies2[i]['genre'])
			movie.append(movies2[i]['year'])
			movie.append(movies2[i]['count'])
			movie.append(movies2[i]['points'])
			movies3.append(movie)

	for i, (title, genre, year, count, points) in enumerate(movies3, start=1):
		listBox.insert("", "end", values=(i, title, genre, year, count, points))
	

	scores.mainloop()


def displayPosters(indexes):
	index2 = indexes[1]
	index1 = indexes[0]
	path = 'movieposters/'
	img1 = path + movies[index1]['poster']
	img2 = path + movies[index2]['poster']
	
	win= Tk()

	w = 800 # width for the Tk root
	h = 750 # height for the Tk root

	# get screen width and height
	ws = win.winfo_screenwidth() # width of the screen
	hs = win.winfo_screenheight() # height of the screen

	# calculate x and y coordinates for the Tk root window
	x = (ws/2) - (w/2)
	y = (hs/2) - (h/2)

	# set the dimensions of the screen 
	# and where it is placed
	# win.geometry('%dx%d+%d+%d' % (w, h, x, y))
	win.geometry('%dx%d+%d+%d' % (ws, hs, ws, hs))

	# win.geometry('800x750')
	win.title('Movie Rankings')
	Label(win, text= "Which movie would you rather watch ?", font= ('Aerial 17 bold italic')).pack(pady= 30)

	def quit():
		win.destroy()

	top = Frame(win)
	bottom = Frame(win)
	top.pack(side=TOP)
	bottom.pack(side=BOTTOM)
	lists = Frame(win)
	lists.pack(in_=top, side=BOTTOM)

	ttk.Button(win, text='Next Ranking',  command=quit).pack(in_=top, side=TOP)

	movies2 = sorted(movies, key=lambda item: item['points'], reverse=True)
	
	num1 = movies2.index(movies[index1]) + 1
	num2 = movies2.index(movies[index2]) + 1

	ttk.Button(win, text= '#' + str(num1) + ': ' + movies[index1]['title'] + ' (' +  movies[index1]['year'] + ')', command=  lambda i = indexes : firstMovieChosen(i)).pack(in_=top, side=LEFT)
	if movies[index1]['rewatch'] == 0:
		ttk.Button(win, text= 'Rewatch?', command=lambda i = index1 : rewatch(i)).pack(in_=lists, side=LEFT)
	else:
		ttk.Button(win, text= 'Remove Rewatch?', command=lambda i = index1 : unRewatch(i)).pack(in_=lists, side=LEFT)
	ttk.Button(win, text= '#' + str(num2) + ': ' + movies[index2]['title'] + ' (' +  movies[index2]['year'] + ')', command=lambda i = indexes : secondMovieChosen(i)).pack(in_=top, side=LEFT)
	if movies[index2]['rewatch'] == 0:
		ttk.Button(win, text= 'Rewatch?', command=lambda i = index2 : rewatch(i)).pack(in_=lists, side=LEFT)
	else:
		ttk.Button(win, text= 'Remove Rewatch?', command=lambda i = index2 : rewatch(i)).pack(in_=lists, side=LEFT)
	ttk.Button(win, text= 'View Ranked List', command=orderedList).pack(in_=bottom, side=BOTTOM)
	ttk.Button(win, text= 'View Rewatch List', command=moviesToRewatch).pack(in_=bottom, side=BOTTOM)
	
	
	canvas = Canvas(win)      
	canvas.pack(fill=BOTH, expand=1, side=LEFT)   
	
	basewidth = 350
	img = Image.open(img1)
	wpercent = (basewidth/float(img.size[0]))
	hsize = int((float(img.size[1])*float(wpercent)))
	img = img.resize((basewidth,hsize), Image.ANTIALIAS)

	first = ImageTk.PhotoImage(img)   
	canvas.create_image(0,0, anchor=NW, image=first) 

	#second
	canvas2 = Canvas(win)      
	canvas2.pack(fill=BOTH, expand=1, side=RIGHT)   
	
	basewidth2 = 350
	img2 = Image.open(img2)
	wpercent2 = (basewidth/float(img2.size[0]))
	hsize2 = int((float(img2.size[1])*float(wpercent2)))
	img2 = img2.resize((basewidth2,hsize2), Image.ANTIALIAS)

	second = ImageTk.PhotoImage(img2)   
	canvas2.create_image(0,0, anchor=NW, image=second) 

	
	win.mainloop()

while True:
	indexes = []
	movies = []
	movieCount = []
	movieCount.append(readMovies())
	indexes = getRandomMovie(movieCount)
	displayPosters(indexes)
