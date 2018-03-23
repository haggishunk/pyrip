#!/bin/python
import os
import argparse
import subprocess
import xmltodict
import pprint
import re

CDDA2WAV = '/usr/bin/cdda2wav'
LAME = '/usr/bin/lame'


class Ripper:

    def __init__(self, dev='/dev/sr0', loc=os.getcwd()):
        self.dev = dev
        self.loc = os.path.abspath(loc)
        return

    def ExecuteCmd(self, cmd_args):
        print('\nExecuting command:\n{0}\n'.format(' '.join(cmd_args)))
        try:
            popen = subprocess.Popen(args=cmd_args)
            retcode = popen.wait()
        except ValueError as err:
            result = False
            print('Bad arguments: {0}'.format(cmd_args))
        except OSError as err:
            result = False
            print('OS-related issue: {0}'.format(err.args))
        except Exception as err:
            result = False
            print('Other error: {0}'.format(err.args))
        else:
            print('\nCommand executed successfully with return code: {0}\n'.
                  format(retcode))
            result = True
        return result

    def CDRip(self):
        cdda2wav_args = [
         CDDA2WAV,
         '-O', 'wav',
         '-paranoia',
         '--alltracks',
         '-cddb', '1',
         'cddbp-server=freedb.freedb.org',
         'cddbp-port=8880',
         'dev={0}'.format(self.dev),
         '{0}/'.format(self.loc)
        ]
        self.ripped = self.ExecuteCmd(cdda2wav_args)
        return

    def ConvertToMP3(self):
        self.converted = {}
        # get all wav files in target directory
        files = [os.path.join(self.loc, x) for x in os.listdir(self.loc) if '.wav' in x]
        for wavfile in files:
            mp3file = wavfile.replace('.wav', '.mp3')
            lame_args = [
             LAME,
             wavfile,
             mp3file,
            ]
            self.converted[mp3file] = self.ExecuteCmd(lame_args)
        return

    def GetInfoCD(self):
        cdindex = [os.path.join(self.loc, indexfile) for indexfile in os.listdir(self.loc) if '.cdindex' in indexfile][0]
        with open(cdindex, 'rb') as info_file:
            self.cdinfo = xmltodict.parse(info_file)
        self.artist = self.cdinfo['CDInfo']['SingleArtistCD']['Artist']
        self.album = self.cdinfo['CDInfo']['Title']
        self.namemap = {}
        for track in self.cdinfo['CDInfo']['SingleArtistCD']['Track']:
            track_no = int(track['@Num'])
            track_name = track['Name']
            formatted_track = '{0:02} - {1}.mp3'.format(track_no, track_name)
            self.namemap[track_no] = os.path.join(self.loc, formatted_track)
        return

    def NameTracks(self, use_converted_dict=True):
        self.GetInfoCD()
        print(self.artist, self.album)

        # gather source track filenames that were successfully converted to MP3
        if use_converted_dict:
            self.trackmap = dict((os.path.join(self.loc, k), TrackNo(k)) for (k, v) in iter(self.converted.items()) if v is True)
        else:
            self.trackmap = dict((os.path.join(self.loc, x), TrackNo(x)) for x in os.listdir(self.loc) if '.mp3' in x)

        for track, no in self.trackmap.items():
            try:
                os.rename(track, self.namemap[no])
                print(os.path.basename(self.namemap[no]))
            except Exception as err:
                print('Failed rename: {0}'.format(err))
        return


def TrackNo(filename):
    try:
        # pull out last digits before file extension
        number = int(re.match('.*_(\d+)\.\w+', filename)[1])
    except Exception as err:
        print('Fault getting trackno: {0}'.format(err))
        return
    else:
        return number


def Main():
    # get args
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='specify the destination for the ripped WAVs and converted MP3s')
    args = parser.parse_args()

    rip = Ripper(loc=args.directory)
    rip.CDRip()
    rip.ConvertToMP3()
    rip.NameTracks()
    return

if __name__ == '__main__':
    Main()
