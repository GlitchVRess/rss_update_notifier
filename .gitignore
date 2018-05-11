# rss_update_notifier
This script is intended to eliminate the need to check webcomics/webserials manually. I currently run this from my server using a cronjob, which may be your best bet.

You store the smtp, recipients, and rss_feed urls within the config file. The scrip pulls from these, checks if a local file's contents matches the most recent post
from each of the rss_feed's, if it does not, it creates an updated file and sends an email to the provided emails. I do not send the url for the comic as I currently
send an email to my cellular provider's text gateway to receive this update as a text message. Sending a url through that text tended to flag their spam filters.

I am attempting to follow PEP 8 style guidelines, though the future module may not be the best representation of this at this time.

When adding sender details or recipent details to the config file, the information should be added as follows:
    sender_details = NameToShowOnEmail EmailUserOrTheThingBeforethe@Symbol DomainNameOrTheThingAfterThe@Symbol
    recipients = NameToShowOnEmail EmailUserOrTheThingBeforethe@Symbol DomainNameOrTheThingAfterThe@Symbol; NameToShowOnEmail EmailUserOrTheThingBeforethe@Symbol DomainNameOrTheThingAfterThe@Symbol

All recipients should be seperated by a semicolon and one space.

The error log is currently used in case the script is unable to send an email out.

If you add a new recipient to the config file, you will need to delete the lastupdate.pkl file that is currently in place.

IMPORTANT:
Make sure to rename your version of sample_config.txt to config.txt


When installing, use install -r requirements.txt to install the required modules.

