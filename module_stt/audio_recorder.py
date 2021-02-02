# -*- coding: utf-8 -*-
"""
Created on Wed Jan 27 19:22:57 2021

@author: ARTURO
"""

#!/usr/bin/env python3
"""Create a recording with arbitrary duration.
The soundfile module (https://PySoundFile.readthedocs.io/) has to be installed!
"""
import argparse
import tempfile
import queue
import sys


import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)

#watson's IBM dependecies
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

#STT authetifiacation
apikey = 'p8wI4OwB4XeAUz8Qz594aGuTc9MQg535V0KoJQp6QaHc'
url = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/bda46712-672c-43e9-b6cb-9fb09a13e226'

authenticator = IAMAuthenticator(apikey)
stt = SpeechToTextV1(authenticator = authenticator)

stt.set_service_url(url)


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'filename', nargs='?', metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate')
parser.add_argument(
    '-c', '--channels', type=int, default=1, help='number of input channels')
parser.add_argument(
    '-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
args = parser.parse_args(remaining)

q = queue.Queue()


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info['default_samplerate'])
    if args.filename is None:
        #args.filename = tempfile.mktemp(prefix='delme_rec_unlimited_',
        #                                suffix='.wav', dir='')
       args.filename = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                       suffix='.wav', dir='')
       

    # Make sure the file is opened before recording anything:
    with sf.SoundFile(args.filename, mode='x', samplerate=args.samplerate,
                      channels=args.channels, subtype=args.subtype) as file:
        with sd.InputStream(samplerate=args.samplerate, device=args.device,
                            channels=args.channels, callback=callback):
            print('#' * 80)
            print('press Ctrl+C to stop the recording')
            print('#' * 80)
            while True:
                file.write(q.get())
except KeyboardInterrupt:
    print('\nRecording finished: ' + repr(args.filename))
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
    
#Transcribe Speech to text

with open(args.filename, 'rb') as f:
    res = stt.recognize(audio=f, content_type='audio/wav', model='es-MX_BroadbandModel', continuous=True).get_result()
    

text = res['results'][0]['alternatives'][0]['transcript']    
    