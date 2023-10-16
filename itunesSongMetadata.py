from bs4 import BeautifulSoup
import music_tag
from pathlib import Path
from urllib.parse import unquote
import os

def get_db_path(dbID):
    while True:
        path = Path(input('Enter the path to the %s: ' % dbID))
        if not path.is_file():
            print(str(path) + ' is not a file. Try again.')
        else: break
    return path

itdb_path = get_db_path('Itunes database')
print('\nParsing Itunes library. This may take a while.')
with open(itdb_path, 'r', encoding="utf-8") as f: soup = BeautifulSoup(f, 'lxml-xml')

songs = soup.dict.dict.find_all('dict') # yields result set of media files to loop through

map = [
    # (music_tag, iTunes field)
    ('album', 'Album'),
    ('albumartist', 'Album Artist'),
    ('artist', 'Artist'),
    ('compilation', 'Compilation'),
    ('composer', 'Composer'),
    ('discnumber', 'Number'),
    ('genre', 'Genre'),
    ('lyrics', 'Lyrics'),
    ('totaldiscs', 'Disc Count'),
    ('totaltracks', 'Track Count'),
    ('tracknumber', 'Track Number'),
    ('tracktitle', 'Name'),
    ('year', 'Year'),
    ('isrc', 'ISRC'),
]

it_root_music_path = unquote(soup.find('key', text='Music Folder').next_sibling.text)


for it_song_entry in songs:
    try:
        name = it_song_entry.find('key', string='Name').next_sibling.text
        org_song_path = unquote(it_song_entry.find('key', string='Location').next_sibling.text)
    except AttributeError:
        name = it_song_entry.find('key', string='Name').next_sibling.text
        continue

    if not org_song_path.startswith(it_root_music_path):  # excludes non-local content
        continue
    org_song_path = org_song_path.replace('file://', '')
    # check if file exists
    if not os.path.isfile(org_song_path):
        print(f'File not found: {org_song_path}')
        continue
    # load tags from file
    f = music_tag.load_file(org_song_path)
    changed = False
    for tag, lib in map:
        try:
            library_value = it_song_entry.find('key', string=lib).next_sibling.text
        except AttributeError:
            continue

        if tag == 'year':
            try:
                # there is an issue, that year is sometimes stored as a full datetime and music_tag can't handle that
                int(f[tag].value)
            except ValueError:
                f[tag] = library_value
                changed = True
                continue
        # print(f'{tag}: {library_value} vs {f[tag]}')
        if (tag in f and str(f[tag].value) != library_value or tag not in f) and library_value != '' :
            print(f'Changing {tag} from "{f[tag]}" to "{library_value}"')
            f[tag] = library_value
            changed = True
    if changed:
        print(f'Writing changes to {org_song_path}')
        f.save()