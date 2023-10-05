# itunes-navidrome-migration
Python scripts to transfer iTunes history to a new Navidrome installation
## Introduction
These Python scripts will transfer song ratings, play counts, play dates and playlists from an existing iTunes library to a new Navidrome installation.

## Background
Itunes saves its data in a Library.xml file. Navidrome saves its data in up to three different `navidrome.db*` files. The script reads from `Library.xml` and writes the data to the navidrome.db file.

These scripts were tested on Linux using a Library.xml file that came from iTunes on Windows. I'm running the Docker version of Navidrome v0.48.0 & Python version 3.10.6.

I am not sure how it would work on other platforms.

## Known issues
1. If the iTunes database has a star rating for an entry but no play count or play date, then it will not migrate that rating to Navidrome. I'm not sure if this is a common enough situation to bother fixing in the ratings migration script. Let me know if it affects you.

2. Foreign alphabets and characters (e.g. Japanese) may not transfer. See [this issue](https://github.com/Stampede/itunes-navidrome-migration/issues/4) for details.

## Installation
1. You can create a Python virtual environment, or not.
2. Download `itunesPlaylistMigrator.py`, `itunestoND.py` and `requirements.txt` and save to a folder.
3. `$ pip3 install -r requirements.txt`

### Not comfortable with Python?
Put your database files in a drop box or something and I will migrate your iTunes library for $15. Email me at ylh9hhiaq@mozmail.com. For playlists, I'd send you back a web page with your playlists listed and hotlinked. If you want to keep the playlist, just click on its link and it will get added to Navidrome.

## How to use
### Preparing your library
Set up your Navidrome server and copy all the folders and music files from your iTunes library to the Navidrome library. Navidrome will build its own database from scratch based on the file metadata.

The most important thing is that you keep the same directory structure between iTunes and Navidrome libraries. Do not rename, delete or move any files or directories. The script uses the file paths to sync the databases. If you want to reorganize the file structure, do it after you have moved over all your itunes data.

That said, before running the scripts, I found it very helpful to use Music Brainz Picard to clean up file metadata **without moving any files**. Use Navidrome for a week or so and if you have problems finding albums or songs, use Picard or Beets or something to improve the metadata tags for the files that are acting funny.

**Only work on backups until you know the scripts were successful.**

### Migrating play counts, last played date and song ratings
1. Shut down your Navidrome server.
2. Copy the Navidrome database files to the machine with these scripts. In my case there are 3 database files: `navidrome.db`, `navidrome.db-shm` and `navidrome.db-wal` you need any `navidrome.db*` file that you find.
3. Run the first script: `$python3 itunestoND.py`
4. It will prompt you to type the path to the `navidrome.db` and `Library.xml`
5. Wait. For large libraries, it can take a few minutes to crunch all the data in `Library.xml`.
6. When it's done, your Navidrome database files may be collapsed into a single `navidrome.db` file. This is OK.
7. **On the machine with the ND server:** delete the 3 database files, then copy over the `navidrome.db` file from the script. Put it in their place.
8. Start your Navidrome server to make sure everything worked correctly. You should now have song ratings and play counts.

The script will also generate a file called `IT_file_correlations.py`. If you don't want to move over your iTunes playlists, you can just delete this.

### Migrating iTunes playlists
I wrote this as an afterthought, so these instructions are a little weird. This script will not move smart playlists. Because of the way `Library.xml` is structured, there are sometimes "false positives" when looking for playlists. You will be prompted before each playlist is created. If you don't recognize a list, just decline when it asks if you want to transfer it.

1. Backup your Navidrome database like you did for the last script in case something goes wrong.
2. Make sure your Navidrome server is running.
3. The previous script generated a file: `IT_file_correlations.py`. Move that file into the same directory where you have `itunesPlaylistMigrator.py` stored.
4. Run the playlist migrator script: `$ python3 itunesPlaylistMigrator.py`. If your working directory is not the same where `Library.xml` is stored, you will be prompted for the path to `Library.xml`.
5. Answer the prompts for your Navidrome username and password.
6. The script will search for playlists from your iTunes library and prompt if you want to move them to Navidrome.

### Migrating iTunes Song Metadata
This script will add metadata to your songs. iTunes doesn't care about metadata in files and stores everything in it's library. Navidrome uses the metadata in the files to build its database. This script will add the metadata from iTunes to the files.

1. Backup your music files.
2. Run the script: `$ python3 itunesSongMetadata.py`
3. Sync your files again with Navidrome if you executed this script after you already migrated your library or targeted a different directory.

## Acknowledgments
Thanks to the Navidrome developers for their hard work and for putting up with my basic questions on the Discord chat as I worked on this script.

Hopefully these scripts help some people. Feel free to copy / share / improve etc.. As far as I'm concerned, this is public domain.

Hello.