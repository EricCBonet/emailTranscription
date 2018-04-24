# usage: python downloadunreadattachments.py
import email
import imaplib
import os
import time
import ConfigParser

config = ConfigParser.ConfigParser()
config.readfp(open('config.cfg'))

imapServer = config.get('attachmentsdownloader', 'imapServer')
username = config.get('attachmentsdownloader', 'username')
password = config.get('attachmentsdownloader', 'password')
attachmentDir = config.get('attachments', 'dir')
pollingInterval = config.getint('attachmentsdownloader', 'pollingInterval')

class FetchEmail():

    connection = None
    error = None

    def __init__(self, mail_server, username, password):
        self.connection = imaplib.IMAP4_SSL(mail_server)
        self.connection.login(username, password)
        self.connection.select(readonly=False) # so we can mark mails as read

    def close_connection(self):
        """
        Close the connection to the IMAP server
        """
        self.connection.close()

    # returns -1 if no attachment is found else returns attachment path after downloading
    def save_attachment(self, msg, download_folder):
        """
        Given a message, save its attachments to the specified
        download folder (default is /tmp)

        return: file path to attachment
        """
        att_path = "-1"
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            timestr = time.strftime("%Y%m%d%H%M%S") # timestamp to make unique filename
            att_path = os.path.join(download_folder, "{0}-{1}".format(timestr, filename))

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
        return att_path

    def fetch_unread_messages(self):
        """
        Retrieve unread messages
        """
        emails = []
        (result, messages) = self.connection.search(None, 'UnSeen')
        if result == "OK":
            for message in messages[0].split(' '):
                try: 
                    ret, data = self.connection.fetch(message,'(RFC822)')
                except:
                    print "No new emails to read."
                    # self.close_connection()
                    # exit()
                    continue 

                msg = email.message_from_string(data[0][1])
                if isinstance(msg, str) == False:
                    emails.append(msg)
                response, data = self.connection.store(message, '+FLAGS','\\Seen')

            return emails

        self.error = "Failed to retreive emails."
        return emails

    def parse_email_address(self, email_address):
        """
        Helper function to parse out the email address from the message

        return: tuple (name, address). Eg. ('John Doe', 'jdoe@example.com')
        """
        return email.utils.parseaddr(email_address)


def processUnreadEmails():
    client = FetchEmail(imapServer, username, password)
    n = 0 # unread messages count
    d = 0 # download count
    for msg in client.fetch_unread_messages():
        if client.save_attachment(msg, attachmentDir) != "-1":
            d = d + 1
        n = n + 1
    print "Processed {0} unread email(s), downloaded {1} attachment(s)".format(n, d)
    client.close_connection()



# check for new mail every minute
while True:
    print 'Pooling'
    processUnreadEmails()
    time.sleep(pollingInterval)