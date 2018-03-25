"""Main

Initializes Ripper class with supplied directory argument
then rips, converts and renames audio files
"""
from pyrip import ripper
import argparse


def Main():
    # get args
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='specify the destination for the ripped WAVs and converted MP3s')
    args = parser.parse_args()

    rip = ripper.Ripper(loc=args.directory)
    rip.CDRip()
    rip.ConvertToMP3()
    rip.NameTracks()
    return

if __name__ == '__main__':
    Main()
