#!/home/kazasu/programming/python/rss_update_notifier/venv/bin/python

import setproctitle
import feedparser
import pickle
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


def feed_grab(config):
    """ This function pulls the urls from the config file, uses the
    future module to send a request to each of the urls at once, and
    then returns the rss feeds parsed as dictionaries of their
    contents.
    """
    # Pulling urls from config file.
    urls = config.get("rss_feeds", "rss_feed_list").split()

    # Using custom module to send request and receive request for
    # feeds as if it was one request rather than multiple.
    future_calls = [Future(feedparser.parse, rss_url) for rss_url in
                    urls]
    # Assigning the received dictionaries as a list under feeds.
    feeds = [future_obj() for future_obj in future_calls]

    return feeds


def email_me(message, subject, config):
    """ This module pulls the sending email configuration from the
    config file, creates an smtp connection, and then sends out an
    email to the recipients listed in the recipient config containing
    the comic and update tile for any comics updated since the last
    check.
    """
    # Setting up sender_configuration.
    sender_address = config.get("sender_config", "username")
    sender_password = config.get("sender_config", "password")
    sender_host = config.get("sender_config", "host")
    sender_port = config.get("sender_config", "port")
    sender = config.get("sender_config", "sender_details").split()

    # Settting up recipient_configuration. Stored as single string
    # with specific recipients separated by semicolons.
    recipients = config.get("recipients_config",
                            "recipients").split("; ")
    recipients = (recipient.split() for recipient in recipients)

    # Creates an smtp connection and logs in using config details.
    s = smtplib.SMTP(sender_host, sender_port)
    s.starttls()
    s.login(sender_address, sender_password)

    # Iterating through recipients to send an email to each.
    for address in recipients:
        msg = EmailMessage()
        msg.set_content(message)

        msg['subject'] = subject
        # Address() is used to better format the email headers.
        msg['from'] = Address(sender[0], sender[1], sender[2])
        msg['to'] = Address(address[0], address[1], address[2])

        try:
            s.send_message(msg)
        except:
            with open("error_log.txt", "a") as file:
                file.write(datetime.now() + ":    " +
                           traceback.format_exc())

    # Disconnecting SMTP connection.
    s.quit()

setproctitle.setproctitle("rss_update_notifier")

# Sets current working directory to the script's home directory.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Config class creation, checks if able to import from config.txt
config = configparser.ConfigParser()
try:
    config.read("config.txt")
except:
    with open("error_log.txt", "a") as file:
        file.write(datetime.now() + ":    " +
                   traceback.format_exec())
    raise SystemExit(0)

# Dictionary to place RSS feed data into.
feed_data = {}
# List of updated RSS feeds that will be emailed.
email_data = []

# Checks if urls provided are functional.
try:
    feeds = feed_grab(config)
except:
    # Emails trace of error and stops script.
    email_me(traceback.format_exc(), "Comic Update Error", config)
    raise SystemExit(0)

# Places data from feed into dictionary and checks if data is invalid.
try:
    for feed in feeds:
        feed_data[feed['channel']['title']] = (
                                           [feed['items'][0]['title'],
                                            feed['items'][0]['link']])
except:
    # Emails trace of error and stops script.
    email_me(traceback.format_exc(), "Comic Update Error", config)
    raise SystemExit(0)

# Tries to open the pick file and compare old data to new if it exists
try:
    with open('lastupdate.pkl', 'rb') as fp:
        itemlist = pickle.load(fp)
except FileNotFoundError:
    file_check = False
else:
    file_check = True

    # For each rss url it checks to see if the latest update is
    # different from what we have stored in our lastupdate file. If
    # there was no lastupdate file found, it sends an email containing
    # all of the comic's most recent update and creates a new file.
for each in feed_data:
    if file_check is True:
        if feed_data[each][0] != itemlist[each][0]:
            email_data.append(each + ":  " + feed_data[each][0])
    else:
        email_data.append(each + ":  " + feed_data[each][0])

with open('lastupdate.pkl', 'wb') as fp:
    pickle.dump(feed_data, fp)

if email_data:
    email_me("\n".join(email_data), "Comic(s) Updated", config)
