#!/bin/python
import os
import subprocess
import xmltodict
import re

CDDA2WAV = '/usr/bin/cdda2wav'
LAME = '/usr/bin/lame'


class Ripper:

    def __init__(self, dev='/dev/sr0', loc=os.getcwd()):
        self.dev = dev
        self.loc = os.path.abspath(os.path.expanduser(loc))
        if not os.path.exists(self.loc):
            try:
                os.makedirs(self.loc)
            except Exception as err:
                print('Bad destination directory: {0}'.format(err.args))
                exit()

        self.work = os.path.join(self.loc, 'working')
        if not os.path.exists(self.work):
            try:
                os.mkdir(self.work)
            except Exception as err:
                print('Could not create working directory: {0}'.format(err.args))
                exit()
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
        # rip wavs to working directory
        cdda2wav_args = [
         CDDA2WAV,
         '-O', 'wav',
         '-paranoia',
         '--alltracks',
         '-cddb', '1',
         'cddbp-server=freedb.freedb.org',
         'cddbp-port=8880',
         'dev={0}'.format(self.dev),
         '{0}/'.format(self.work)
        ]
        self.ripped = self.ExecuteCmd(cdda2wav_args)
        return

    def ConvertToMP3(self):
        self.converted = {}
        # get all wav files in working directory
        files = [x for x in os.listdir(self.work) if '.wav' in x]
        for wavfile in files:
            mp3file = wavfile.replace('.wav', '.mp3')
            lame_args = [
             LAME,
             os.path.join(self.work, wavfile),
             os.path.join(self.work, mp3file),
            ]
            self.converted[mp3file] = self.ExecuteCmd(lame_args)
        return

    def GetInfoCD(self):
        self.cdindex = '.cdindex'
        self.cddb = '.cddb'
        with open(os.path.join(self.work, self.cdindex), 'rb') as info_file:
            self.cdinfo = xmltodict.parse(info_file)
        self.artist = self.cdinfo['CDInfo']['SingleArtistCD']['Artist']
        self.album = self.cdinfo['CDInfo']['Title']
        self.namemap = {}
        for track in self.cdinfo['CDInfo']['SingleArtistCD']['Track']:
            track_no = int(track['@Num'])
            track_name = track['Name']
            formatted_track = '{0:02} - {1}'.format(track_no, track_name)
            self.namemap[track_no] = formatted_track
        print('Got info for {0}: {1}'.format(self.artist, self.album))
        return

    def NameTracks(self, use_converted_dict=True):
        self.GetInfoCD()
        self.dest = os.path.join(self.loc, self.artist, self.album)
        if not os.path.exists(self.dest):
            try:
                os.makedirs(self.dest)
            except Exception as err:
                print('Could not create final destination: {0}'.format(err.args))
                exit()
        self.TransferFile(self.cdindex)
        self.TransferFile(self.cddb)

        # gather source track filenames that were successfully converted to MP3
        if use_converted_dict:
            self.trackmap = dict((os.path.splitext(k)[0], TrackNo(k)) for (k, v) in iter(self.converted.items()) if v is True)
        else:
            self.trackmap = dict((os.path.splitext(x)[0], TrackNo(x)) for x in os.listdir(self.work) if '.mp3' in x)
        for track, no in self.trackmap.items():
            final_track = self.namemap[no]
            self.TransferFile('{0}.mp3'.format(track), '{0}.mp3'.format(final_track))
            self.TransferFile('{0}.wav'.format(track), '{0}.wav'.format(final_track))
            self.TransferFile('{0}.inf'.format(track), '{0}.inf'.format(final_track))
            print(final_track)
        return

    def TransferFile(self, basename, newname=None):
        if newname is None:
            newname = basename
        try:
            print('Moving {0} to {1}'.format(os.path.join(self.work, basename), os.path.join(self.dest, newname)))
            os.rename(os.path.join(self.work, basename), os.path.join(self.dest, newname))
        except Exception as err:
            print('No luck transferring file: {0}'.format(err.args))
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
