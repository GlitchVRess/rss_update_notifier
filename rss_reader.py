import setproctitle
import feedparser
import sqlite3
import traceback
import smtplib
import requests
import configparser
import sys
import os
from datetime import datetime
from email.message import EmailMessage
from email.headerregistry import Address
from future import Future


class RSSReader:
    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        setproctitle.setproctitle("rss_update_notifier")
        self.config = configparser.ConfigParser()
        self.config.read("config.txt")
        self.feeds = self.configure_feeds()
        self.sender = self.configure_sender()
        self.recipients = self.configure_recipients()
        self.configure_db()
        self.compare_feeds()

    def configure_feeds(self):
        """ This function pulls the urls from the config file, uses the
        future module to send a request to each of the urls at once, and
        then returns the rss feeds parsed as dictionaries of their
        contents.
        """
        # Pulling urls from config file.
        urls = self.config.get("rss_feeds", "rss_feed_list").split()

        # Using custom module to send request and receive request for
        # feeds as if it was one request rather than multiple.
        future_calls = [Future(feedparser.parse, rss_url) for rss_url in
                        urls]
        # Assigning the received dictionaries as a list under feeds.
        feeds = [future_obj() for future_obj in future_calls]

        return feeds

    def configure_sender(self):
        sender = {}
        sender['address'] = self.config.get("sender_config", "username")
        sender['password'] = self.config.get("sender_config", "password")
        sender['host'] = self.config.get("sender_config", "host")
        sender['port'] = self.config.get("sender_config", "port")

        address = self.config.get("sender_config", "sender_details").split()
        sender['details'] = Address(address[0], address[1], address[2])
        return sender

    def configure_recipients(self):
            recipients_initial = self.config.get("recipients_config",
                                                 "recipients").split("; ")
            recipients = []

            for recipient in recipients_initial:
                address = recipient.split()
                recipients.append(Address(address[0], address[1], address[2]))

            return recipients

    def send_mail(self, message):
        smtp = smtplib.SMTP(self.sender['host'],
                            self.sender['port'])
        smtp.starttls()
        smtp.login(self.sender['address'], self.sender['password'])

        for recipient in self.recipients:
            msg = EmailMessage()
            msg.set_content(message)
            msg['subject'] = "Comic(s) Updated"
            msg['from'] = self.sender['details']
            msg['to'] = recipient

            try:
                smtp.send_message(msg)
            except Exception as e:
                with open("error_log.txt", "a") as file:
                    file.write(datetime.now() + ":    " +
                               traceback.format_exc())

        smtp.quit()

    def cursor_from_db(self):
        connection = sqlite3.connect("./data/rss_feeds.sqlite3")
        cursor = connection.cursor()

        return cursor, connection

    def configure_db(self):
        cursor, conn = self.cursor_from_db()
        cursor.execute('CREATE TABLE IF NOT EXISTS rss '
                       + '(id INTEGER PRIMARY KEY, title text, '
                       + 'last_update_title text, last_update_url)')

        conn.commit()
        conn.close()

    def compare_feeds(self):
        updates = False
        feed_data = []

        try:
            for feed in self.feeds:
                feed_data.append({
                                    'title': feed['channel']['title'],
                                    'post_title': feed['items'][0]['title'],
                                    'post_url': feed['items'][0]['link'],
                                    'updated': False})
        except Exception as e:
            raise SystemExit(0)

        cursor, conn = self.cursor_from_db()

        for i, feed in enumerate(feed_data):
            cursor.execute("SELECT * FROM rss WHERE title=?", (feed['title'],))
            row = cursor.fetchone()
            if row:
                if row[2] is not feed['post_url']:
                    query = ''' UPDATE rss
                            SET last_update_title = ?,
                            last_update_url = ?
                            WHERE title = ? '''
                    cursor.execute(query, (feed['post_title'],
                                           feed['post_url'],
                                           feed['title']))
                    conn.commit()
                    feed_data[i]['updated'] = True
                    updates = True
            else:
                query = '''
                    INSERT INTO rss(title, last_update_title, last_update_url)
                    VALUES(?,?,?)'''

                cursor.execute(query, (feed['title'],
                                       feed['post_title'],
                                       feed['post_url']))
                conn.commit()
                feed_data[i]['updated'] = True
                updates = True

        conn.close()

        if updates is True:
            email_data = []
            for feed in feed_data:
                if feed['updated'] is True:
                    email_data.append("{}:   {} - {}".format(
                                                    feed,
                                                    feed['post_title'],
                                                    feed['post_url']))

            email_data = "\n".join(email_data)
            self.send_mail(email_data)


if __name__ == '__main__':
    reader = RSSReader()
