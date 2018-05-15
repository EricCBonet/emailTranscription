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
import errno

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

config = ConfigParser.ConfigParser()
config.readfp(open('config.cfg'))

attachmentDir = config.get('attachments', 'dir')
tempDir = config.get('attachmentsprocessor', 'tempDir')
transcriptionFileName =  config.get('attachmentsprocessor', 'transcriptionFileName')
transcriptionErrorFileName =  config.get('attachmentsprocessor', 'transcriptionErrorFileName')

# in seconds to prevent dirty file read (IOError: [Errno 13] Permission denied: error)
delayBeforeOpening = config.getfloat('attachmentsprocessor', 'delayBeforeOpening')


def processZip(newFile):
    print('newFile = '+ newFile)
    timestr = time.strftime("%Y%m%d%H%M%S") # timestamp to make unique filename
    destinationTempDir = "{0}/{1}-{2}".format(tempDir, timestr, ntpath.basename(newFile)[:-4])
    print('destinationTempDir = ' + destinationTempDir)

    # extract all files
    try:  # first try if a zip file is attached
        with zipfile.ZipFile(newFile, "r") as f:
            # it gets sent to the tempDir!
            # i need to send it to the destinationTempDir
            f.extractall(destinationTempDir)
    except: # if not then move the other files to the temp directory
	print('not a zip file')
        if not os.path.exists(destinationTempDir):
            try:
                os.makedirs(destinationTempDir)
                print('making a new directory')
            except OSError as exc: # Guard against race condition
               print( 'cannot make temp directory')
               if exc.errno != errno.EEXIST:
                    raise

    # run ffmpeg on all files except .txt and .wav file
    for filename in os.listdir('attachments'):
        if not filename.endswith ('.txt') and not filename.endswith ('.wav'):
            print(os.path.join(filename))
            audioFile = os.path.join(destinationTempDir, filename)

            audioFileWithoutExtension = os.path.splitext(audioFile)[0]     
            print(['ffmpeg', '-i', newFile, '-vn','-ar','44100', '-ac','2','-ab','192k','-f', 'wav', '{0}.wav'.format(audioFileWithoutExtension) ])
            subprocess.call(['ffmpeg', '-i', newFile, '-vn','-ar','44100', '-ac','2','-ab','192k','-f', 'wav', '{0}.wav'.format(audioFileWithoutExtension) ])


    # copy txt file as it is to resultTempDir
    resultTempDir =  "{0}-result".format(destinationTempDir)
    print(resultTempDir)
    os.mkdir(resultTempDir)
    for filename in os.listdir(resultTempDir):
        filePath = os.path.join(resultTempDir, filename)
        if filename.endswith ('.txt'):
            shutil.copy(filePath, resultTempDir)

    # get email addresss from the directory name
    emailReceipient =  resultTempDir.split('-')[1]


    # delete files in the attachments directory
    for filename in os.listdir('attachments'):
        os.remove(os.path.join('attachments',filename))

    # process wav files and copy output to resultTempDir
    with open(os.path.join(resultTempDir, transcriptionFileName), 'w') as logfile:
        with open(os.path.join(resultTempDir, transcriptionErrorFileName), 'w') as errorfile:
            subprocess.call(['python', 'speechtotext.py', destinationTempDir], stdout=logfile, stderr=errorfile)

    # Email resultTempDir to emailReceipient
    subprocess.call(['python', 'emaildirectory.py', '-d', resultTempDir, '-r', emailReceipient])


class CreateHandler(FileSystemEventHandler):
    def on_created(self, event):
        time.sleep(delayBeforeOpening)
       # if not event.src_path.endswith('.zip'):
        #    print '{0} is not a zip file'.format(event.src_path)
         #   return
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




