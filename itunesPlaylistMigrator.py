#! /usr/bin/env python

# itunesPlaylistMigrator.py - Used in conjunction with itunestoND.py
# First run that script, then run this one while you have your Navidrome server running.
# It will parse the Itunes library XML file and use the Navidrome API to transfer your playlists.

from pathlib import Path
import sys, requests, urllib.parse, random, re, string, json
from bs4 import BeautifulSoup
import pyinputplus as pyip
from hashlib import md5

try:
    from IT_file_correlations import *
    print('File correlations between the databases successfully imported.')
except ModuleNotFoundError:
    print('You need to put the IT_file_correlations.py file in the same directory as this script.')
    sys.exit(1)

def send_api_request(endpoint, **kwargs):
    api_args = {'f': 'json', 'u': username, 'v': '1.16.1', 'c': 'python'}
    api_args.update(kwargs)

    pool = string.ascii_letters + string.digits
    salt = ''.join(random.choice(pool) for i in range(7))
    token = md5((password + salt).encode('utf-8')).hexdigest()

    api_args.update({'t': token, 's': salt})

    try:
        res = requests.get(server_url + endpoint, params=api_args)
        res.raise_for_status()

    except:
        print(f"Could not reach Navidrome Server. You entered {server_url.partition('rest/')[0]}")
        print('Make sure that address is correct.')
        print()
        if pyip.inputYesNo(prompt='Is the server running? ') == 'yes':
            print('Well you better go catch it!')
        else:
            print('Start the Navidrome server and try again.')
        return False

    try:
        res = json.loads(res.text)['subsonic-response']
        if res['status'] == 'ok':
            return res
        else:
            print('\nSomething went wrong with the Navidrome server.\n')
            print(f'Message: {res["error"]["message"]}. Code {res["error"]["code"]}.')
            return False
    except KeyError:
        print('Seems that the address you entered does not go to a navidrome server.')

def transfer_playlist_to_nd(itunes_list):
    pass

login_successful = False

while not login_successful:
    print()
    server_url = input('Enter the address to your navidrome server: ')
    username = input('Enter your Navidrome username: ')
    password = pyip.inputPassword(prompt='Enter the password to your Navidrome account: ')

    if not server_url.startswith('http'):
        server_url = 'http://' + server_url
    if server_url.endswith('/'): server_url = server_url[:-1]
    server_url += '/rest/'
    login_successful = send_api_request('ping')

    if login_successful: print('\nConnection to server successful.')

#Parse library File
it_db_path = Path.cwd() / 'Library.xml'
while not it_db_path.is_file():
    print('I did not find a file at %s .' % str(it_db_path))
    it_db_path = Path(input('Enter the absolute path to the itunes library: '))

print('Using %s for the itunes library.' % str(it_db_path))

with open(it_db_path, 'r') as f: soup = BeautifulSoup(f, 'lxml-xml')
playlists = soup.array.find_all('dict', recursive=False)

# Cycle through playlists and choose whether to add them to Navidrome

playlists_to_skip = ('Library', 'Downloaded', 'Music', 'Movies', 'TV Shows', 'Podcasts', 'Audiobooks', 'Tagged', 'Genius')
for plist in playlists:
    if plist.find('key', text='Distinguished Kind'): continue # these are special playlists unique to Itunes
    
    playlist_name = plist.find('key', text='Name').find_next('string').text
    if playlist_name in playlists_to_skip: continue
    if plist.find('key', text='Smart Info'): continue
    
    try:
        playlist_tracks = plist.array.find_all('dict')
    except AttributeError:
        continue

    print(f'\nA playlist named {playlist_name} contains {len(playlist_tracks)} tracks.')
    should_we_keep_playlist = pyip.inputYesNo(prompt='Do you want to move it to Navidrome? ')
    if should_we_keep_playlist == 'no': continue

    create_playlist_reply = send_api_request('createPlaylist', name=playlist_name)
    if not create_playlist_reply:
        print('Something went wrong when trying to create the %s playlist.' % playlist_name)

    else:
        ND_playlist_id = create_playlist_reply['playlist']['id']
        it_track_ids = [int(track.integer.text) for track in playlist_tracks]
        ND_track_ids = [itunes_correlations[x] for x in it_track_ids]

        add_tracks_reply = send_api_request('updatePlaylist', playlistId=ND_playlist_id, songIdToAdd=ND_track_ids)



# This works to create a playlist.
'''Here is what it returns:

>>> serverReply = send_api_request('createPlaylist', name='my test playlist')

{'status': 'ok',
 'version': '1.16.1',
 'type': 'navidrome',
 'serverVersion': '0.48.0 (af5c2b5a)',
 'playlist': {'id': '371d5395-8462-4453-afb7-cebd2013eaf1',
  'name': 'my test playlist',
  'songCount': 0,
  'duration': 0,
  'public': False,
  'owner': 'usernam',
  'created': '2022-12-23T23:48:34.936169089Z',
  'changed': '2022-12-23T23:48:34.936171839Z'}}
  '''

# This works to add multiple songs at one time. Note that you can put multiple song IDs in a list and it works OK:
'''

updatingReply = send_api_request('updatePlaylist', playlistId='91866b80-1cf6-4ca3-8e59-acec4fd29282', songIdToAdd=['9b4f1e2a7cb79adbef220deac179c
    ...: 254', '7465599c97cdc84d347123c96b43899d', '14ef255126037deab2ab5380e974b11f'])

returns: 
{'status': 'ok',
 'version': '1.16.1',
 'type': 'navidrome',
 'serverVersion': '0.48.0 (af5c2b5a)'}
'''
