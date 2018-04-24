# pip install watchdog
# apt-get install ffmpeg
# usage: 
# python processattachments.py
import zipfile
import ntpath
import shutil
import time
import os
import subprocess
import sys
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import speech_recognition as sr
import json
import codecs
import ConfigParser

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

config = ConfigParser.ConfigParser()
config.readfp(open('config.cfg'))

attachmentDir = config.get('attachments', 'dir')
tempDir = config.get('attachmentsprocessor', 'tempDir')
transcriptionFileName =  config.get('attachmentsprocessor', 'transcriptionFileName')
transcriptionErrorFileName =  config.get('attachmentsprocessor', 'transcriptionErrorFileName')
emailReceipient =  config.get('attachmentsprocessor', 'emailReceipient')
# in seconds to prevent dirty file read (IOError: [Errno 13] Permission denied: error)
delayBeforeOpening = config.getfloat('attachmentsprocessor', 'delayBeforeOpening')


def processZip(zipfilePath):
    timestr = time.strftime("%Y%m%d%H%M%S") # timestamp to make unique filename
    destinationTempDir = "{0}/{1}-{2}".format(tempDir, timestr, ntpath.basename(zipfilePath)[:-4])


    # extract all files
    with zipfile.ZipFile(zipfilePath, "r") as f:
        f.extractall(destinationTempDir)

    # run ffmpeg on all files except .txt and .wav file
    for filename in os.listdir(destinationTempDir):
        if not filename.endswith ('.txt') and not filename.endswith ('.wav'):
            # print(os.path.join(directory, filename))
            audioFile = os.path.join(destinationTempDir, filename)
            audioFileWithoutExtension = os.path.splitext(audioFile)[0] 
            subprocess.call(['ffmpeg', '-i', audioFile, '-vn','-ar','44100', '-ac','2','-ab','192k','-f', 'wav', '{0}.wav'.format(audioFileWithoutExtension) ])

    # copy txt file as it is to resultTempDir
    resultTempDir =  "{0}-result".format(destinationTempDir)
    os.mkdir(resultTempDir)
    for filename in os.listdir(destinationTempDir):
        filePath = os.path.join(destinationTempDir, filename)
        if filename.endswith ('.txt'):
            shutil.copy(filePath, resultTempDir)

    # process wav files and copy output to resultTempDir
    with open(os.path.join(resultTempDir, transcriptionFileName), 'w') as logfile:
        with open(os.path.join(resultTempDir, transcriptionErrorFileName), 'w') as errorfile:
            subprocess.call(['python', 'speechtotext.py', destinationTempDir], stdout=logfile, stderr=errorfile)


    # Email resultTempDir to emailReceipient
    subprocess.call(['python', 'emaildirectory.py', '-d', resultTempDir, '-r', emailReceipient])


class CreateHandler(FileSystemEventHandler):
    def on_created(self, event):
        time.sleep(delayBeforeOpening)
        if not event.src_path.endswith('.zip'):
            print '{0} is not a zip file'.format(event.src_path)
            return
        try:
            processZip(event.src_path)
        except:
            logging.exception('processZipException') # log exception
        print '............................................'


if __name__ == '__main__':
    event_handler = CreateHandler()
    observer = Observer()
    observer.schedule(event_handler, attachmentDir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()




