import argparse
import pyrip.ripper

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='specify the destination for the ripped WAVs and converted MP3s')
    args = parser.parse_args()

    rip = pyrip.ripper.Ripper(loc=args.directory)
    rip.CDRip()
    rip.ConvertToMP3()
    rip.NameTracks()
