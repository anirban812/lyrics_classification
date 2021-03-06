# Cleaning the data which has been scraped from songlyrics.com
import sys
import MySQLdb
import re
import pandas as pd
import collections
from sklearn.model_selection import train_test_split

genres_list = ['Rock', 'Pop', 'Hip Hop/Rap', 'R&B;', 'Electronic', 'Country', 'Jazz', 'Blues', 'Christian', 'Folk']
better_oracle_genres = ['Rock', 'Pop', 'Hip Hop/Rap', 'R&B;', 'Country', 'Jazz', 'Blues', 'Christian']
accepted_characters = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\',.\n\r ')
SONG_LIMIT_PER_GENRE = 10000	# not taking more than these per genre to have a homogenous mix of training data

# genre, url, lyrics
def get_songs_by_genre(genre_of_interest, db_cursor):
	"""
	@param: genre_of_interest: The genre you are interested in, as a string
	Send query to db for a particular genre
	"""
	query = "select lyrics from song where genre = '%s'" %genre_of_interest
	db_cursor.execute(query)
	data = db_cursor.fetchall()
	return data

def get_data(genres=genres_list):
	"""
	@param genres: List of genres (strings) to collect from the db
	Gets data from the db, arranges it in the form ('lyrics', genre_class), where genre_class is an int representing the genre
	It correspondds to the index in the genres list. Returns a Panda object (dataframe).
	"""
	print 'establishing connection to db...',
	db = MySQLdb.connect(host="localhost", db="cs221_nlp", read_default_file='~/.my.cnf')
	db_cursor = db.cursor()
	print 'done!'
	dataset = []
	for label, genre in enumerate(genres):
		data = get_songs_by_genre(genre, db_cursor)
		for song in data:
			# song is a singleton tuple (since the db query returns only tuples), so need to extract
			dataset.append([song[0], label])	# <----- REMEMBER THAT THE GENRE IS THE LABEL (0..9), NOT THE STRING!
	# convert to pandas
	dataset = pd.DataFrame.from_records(dataset, columns=['lyrics', 'genre'])
	return dataset

def create_train_test(dataset):
	# returns two datasets, train which is randomly sampled 80% of the set and test which is 20%
	train, test = train_test_split(dataset, test_size = 0.2)
	return (train, test)

def create_corpus_for_glove(dataset, frac=0.7):
	# will take a random 70% sample of a dataset (or whatever fraction you supply as 'frac')
	# and concatenate each and every song into one huge corpus
	# it will also remove text characters and non-spaces and non-alphabets 
	# will also convert everything to lowercase
	# ideally you want to save this to a file and then run ./demo.sh to train GloVe vectors on it
	import random
	text = dataset['lyrics'].tolist()
	rtextsample = random.sample(text, int(frac*len(text)))
	textcorpus = ' '.join([re.sub(r"[^\s\w]|\d", '', t.lower().replace('\n', ' ')) for t in rtextsample])
	return textcorpus


if __name__ == "__main__":
	# read in the songs, straight from the db
	data = get_data(genres=better_oracle_genres)

	# convert them into lists
	all_lyrics = data['lyrics'].tolist()
	all_lyrics_genres = data['genre'].tolist()

	# process them: one by one go through each, and process the lyrics. Then append to the corresponding genre list
	songs_by_genre = collections.defaultdict(int)
	songs_master_list = []

	for i in range(len(all_lyrics)):
		if i%1000 == 0:
			print 'Finished processing song #%d' %i
		current_genre = all_lyrics_genres[i]
		if (songs_by_genre[current_genre] > SONG_LIMIT_PER_GENRE):
			continue
		current_song = all_lyrics[i]
		# filter using knowledge from http://stackoverflow.com/questions/8689795/how-can-i-remove-non-ascii-characters-but-leave-periods-and-spaces-using-python
		current_song = filter(lambda x: x in accepted_characters, current_song)		# get rid of characters which aren't in our guest list
		if not (current_song, current_genre) in songs_master_list:
			# expensive operation but worth it to prevent duplicates
			songs_master_list.append((current_song, current_genre))
			songs_by_genre[current_genre] += 1

	print 'Completed. Number of distinct songs = %d' %len(songs_master_list)
	# Now we have a list of lists containing filtered strings. We need to save them in a form that is easily readable. 
	# Pandas are a good choice
	print 'Saving songs to csv file...',
	final_songs = pd.DataFrame(songs_master_list, columns = ['lyrics', 'genre'])
	with open('songData-Dec3.csv', 'w') as f:
		final_songs.to_csv(f, index=False)
	
	print 'completed! Enjoy your new dataset. Number of songs per genre:'
	for g in songs_by_genre.keys():
		print g, ":", songs_by_genre[g]


