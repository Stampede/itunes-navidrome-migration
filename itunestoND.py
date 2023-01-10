#!/usr/bin/env python

# itunestoND.py - Transfers song ratings, playcounts and play dates from I-Tunes library
# to the Navidrome database

import sys, sqlite3, datetime, re, string, pprint, random
from pathlib import Path
from urllib.parse import unquote
from bs4 import BeautifulSoup

def get_db_path(dbID):
    while True:
        path = Path(input('Enter the path to the %s: ' % dbID))
        if not path.is_file():
            print(str(path) + ' is not a file. Try again.')
        else: break
    return path

def determine_userID(nd_p):
    conn = sqlite3.connect(nd_p)
    cur = conn.cursor()
    cur.execute('SELECT id, user_name FROM user')
    users = cur.fetchall()
    if len(users) == 1:
        print(f'Changes will be applied to the {users[0][1]} Navidrome account.')
    else:
        raise Exception('There needs to be exactly one user account set up with Navidrome. You either have 0, or more than 1 user account.')
    conn.close()
    return users[0][0]

def update_playstats(d1, id, playcount, playdate, rating=0):
    d1.setdefault(id, {})
    d1[id].setdefault('play count', 0)
    d1[id].setdefault('play date', datetime.datetime.fromordinal(1))
    d1[id]['play count'] += playcount
    d1[id]['rating'] = rating

    if playdate > d1[id]['play date']: d1[id].update({'play date': playdate})

def generate_annotation_id(): # random hex number 32 characters long
    character_pool = string.hexdigits[:16]

    id_elements = []
    for char_count in (8, 4, 4, 4, 12):
        id_elements.append(''.join(random.choice(character_pool) for i in range(char_count)))
    return '-'.join(id_elements)

def write_to_annotation(dictionary_with_stats, entry_type):
    annotation_entries = []
    for item_id in dictionary_with_stats:
        this_entry = dictionary_with_stats[item_id]
        
        play_count = this_entry['play count']
        play_date = this_entry['play date'].strftime('%Y-%m-%d %H:%M:%S') # YYYY-MM-DD 24:mm:ss
        rating = this_entry['rating']

        annotation_entries.append((generate_annotation_id(), userID, item_id, entry_type, play_count, play_date, rating, 0, None))

    conn = sqlite3.connect(nddb_path)
    cur = conn.cursor()
    cur.executemany('INSERT INTO annotation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', annotation_entries)
    conn.commit()
    conn.close()
        # cur.executemany('INSERT INTO consumers VALUES (?,?,?,?)', purchases)
        # cur.execute("INSERT INTO consumers VALUES (1,'John Doe','john.doe@xyz.com','A')")

_ = None
while _ != 'proceed':
    print()
    print('This script will migrate certain data from your ITunes library to your Navidrome database.', 
        "Back up all your data in case it doesn't work properly on your setup. NO WARRANTIES. NO PROMISES.", 
        "The script will DELETE existing data you have in your Navidrome database so it can start \"fresh\".", sep='\n')
    print()

    _ = input('Type PROCEED to continue, or Q to quit: ').lower()

    if _ == 'q': print('Good bye.'); sys.exit(0)

nddb_path = get_db_path('Navidrome database')
itdb_path = get_db_path('Itunes database')
print('\nParsing Itunes library. This may take a while.')
with open(itdb_path, 'r') as f: soup = BeautifulSoup(f, 'lxml-xml')

it_root_music_path = unquote(soup.find('key', text='Music Folder').next_sibling.text)
# example output of previous line: 'file://localhost/C:/Users/REDACTED/Music/iTunes/iTunes Music/'

songs = soup.dict.dict.find_all('dict') # yields result set of media files to loop through

song_count = len(songs)
print(f'Found {song_count:,} files in Itunes database to process.')
del(soup)

userID = determine_userID(nddb_path)
songID_correlation = {} # we'll save this for later use to transfer Itunes playlists to ND (another script)
artists = {}            # artists and albums will keep count of plays and play dates for each
albums = {}
files = {}


status_interval = song_count // 8
counter = 0

conn = sqlite3.connect(nddb_path)
cur = conn.cursor()
cur.execute('DELETE FROM annotation')
conn.commit()

for it_song_entry in songs:
    counter += 1    # progress tracking feedback
    if counter % status_interval == 0:
        print(f'{counter:,} files parsed so far of {song_count:,} total songs.')

    # chop off first part of IT path so we can correlate it to the entry in the ND database
    song_path = unquote(it_song_entry.find('key', string='Location').next_sibling.text)
    song_path = re.sub(it_root_music_path, '', song_path)

    try:
        cur.execute('SELECT id, artist_id, album_id FROM media_file WHERE path LIKE "%' + song_path + '"')
        song_id, artist_id, album_id = cur.fetchone()
    except TypeError:
        print(f"Error while parsing {song_path}. Navidrome does not acknowledge that file's existence.")
        print("Maybe Navidrome doesn't like the extension? Skipping.")
        continue


    # correlate Itunes ID with Navidrome ID (for use in a future script)
    it_song_ID = int(it_song_entry.find('key', string='Track ID').next_sibling.text)
    songID_correlation.update({it_song_ID: song_id})
    
    try:    # get rating, play count & date from Itunes
        song_rating = int(it_song_entry.find('key', string='Rating').next_sibling.text)
        song_rating = int(song_rating / 20)
    except AttributeError: song_rating = 0 # rating = 0 (unrated) if it's not rated in itunes
        
    try:
        play_count = int(it_song_entry.find('key', string='Play Count').next_sibling.text)
        last_played = it_song_entry.find('key', string='Play Date UTC').next_sibling.text[:-1] # slice off the trailing 'Z'
        last_played = datetime.datetime.strptime(last_played, '%Y-%m-%dT%H:%M:%S') # convert from string to datetime object. Example string: '2020-01-19T02:24:14Z'
    except AttributeError: continue

    update_playstats(artists, artist_id, play_count, last_played)
    update_playstats(albums, album_id, play_count, last_played)
    update_playstats(files, song_id, play_count, last_played, rating=song_rating)

    

conn.close()

print('Writing changes to database:')
write_to_annotation(artists, 'artist')
print('Done writing artist records to database.')
write_to_annotation(files, 'media_file')
print('Done writing music file records to database.')
write_to_annotation(albums, 'album')
print('Album records saved to database.')

with open('IT_file_correlations.py', 'w') as f:
    f.write('# Following python dictionary correlates the itunes integer ID to the Navidrome file ID for each song.\n')
    f.write('# {ITUNES ID: ND ID} is the format. \n\n')
    f.write('itunes_correlations = ')
    f.write(pprint.pformat(songID_correlation))

print('Navidrome database updated.')
print(f"File correlation index saved to {str(Path.cwd() / 'IT_file_correlations.py')}\n")
print('You can delete it if you want, but I will use it later in a script to transfer playlists from Itunes to Navidrome.')
