# pip install SpeechRecognition
# Example usage: 
# 1) Log result and errors in different files
# python speechtotext.py <directory> > result.csv 2> errorlog.txt
# 2) Print output
# python speechtotext.py <directory>
import sys
import time
import logging
import speech_recognition as sr
import json
import codecs
import os
import ntpath
import ConfigParser
sys.stdout = codecs.getwriter('utf8')(sys.stdout)

config = ConfigParser.ConfigParser()
config.readfp(open('config.cfg'))

targetLanguage = config.get('speechtotext', 'targetLanguage')
GOOGLE_CLOUD_SPEECH_CREDENTIALS = config.get('speechtotext','gceServiceAccount')

r = sr.Recognizer()

def speechToText(AUDIO_FILE):
    filename = ntpath.basename(AUDIO_FILE)
    # use the audio file as the audio source
    with sr.AudioFile(AUDIO_FILE) as source:
        audio = r.record(source)  # read the entire audio file
    # recognize speech using Google Cloud Speech
    try:
        # pass show_all=True to get complete json response with confidence
        # jsonResponse = r.recognize_google_cloud(audio, credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS, language = targetLanguage, show_all=True)
        # {
        #     "results": [
        #         {
        #             "alternatives": [
        #                 {
        #                     "confidence": 0.9843024,
        #                     "transcript": "and I am making a second audio recording because this software should be able to do multiple recordings",
        #                     "words": [
                            
        #                     ]
        #                 }
        #             ]
        #         }
        #     ]
        # }
        transcription = r.recognize_google_cloud(audio, credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS, language = targetLanguage)
        print ",".join([filename, transcription])
    except sr.UnknownValueError:
        print ",".join([filename, "Google Cloud Speech could not understand audio"])
    except sr.RequestError as e:
        print ",".join([filename, "Could not request results from Google Cloud Speech service; {0}".format(e)])



if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    for filename in os.listdir(path):
        if filename.endswith('.wav'):
            filePath = os.path.join(path, filename)
            speechToText(filePath)








