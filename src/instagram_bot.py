import credentials
import praw
import sqlite3
import re
import time
import get_media_id
import rehost
import escape
import sys
import logging
import comments
from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError

logging.basicConfig(filename="logfile.log", format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt="%Y-%m-%d %H:%M:%S")

db = sqlite3.connect('igdb.db')
curs = db.cursor()
user_agent = "Simple script to search for instagram links by /u/drogbafan"
r = praw.Reddit(user_agent=user_agent)
r.login(username=credentials.credentials["REDDIT_USERNAME"], password=credentials.credentials["REDDIT_PASSWORD"])
already_done = []
to_be_done = []
api = InstagramAPI(client_secret=credentials.credentials["CLIENT_SECRET"], access_token=credentials.credentials["ACCESS_TOKEN"])


while True:
    unread = r.get_unread(limit=None)

    for message in unread:
        if re.search(r'\+delete\s', message.body.lower()):
            try:
                the_id = re.findall(r'\+delete\s(.*?)$', message.body.lower())[0]
                logging.debug("The comment id is " + the_id)
                the_id = 't1_' + the_id
                comment = r.get_info(thing_id=the_id)
                comment_parent = r.get_info(thing_id=comment.parent_id)

                if message.author.name == comment_parent.author.name or message.author.name == 'drogbafan':
                    hashcode = re.findall(r'imgrush\.com\/(\S*?)\.(?:mp4|jpe)', comment.body)[0]
                    logging.debug("The hashcode id is " + hashcode)

                    comment.edit("Edited and deleted this comment")
                    comment.delete()

                    try:
                        rehost.delete_rehost(hashcode)
                    except Exception as e:
                        logging.critical("Unable to delete rehosted image because: " + str(e))

                    logging.info("Successfully deleted comment: " + the_id)

                    message.mark_as_read()
                else:
                    logging.debug("Illegitmate delete request by " + message.author.name + " at " + comment.id)
                    message.mark_as_read()
            except Exception as e:
                logging.critical("Unable to delete because: " + str(e))


    for submission in r.get_domain_listing('instagram.com', sort='new',limit=25):
        if len(re.findall('http[s]?://instagram.com/p/\S+|http[s]?://www.instagram.com/p/\S+', str(submission.url))) > 0:
            to_be_done.append(submission)

    for submission in to_be_done:
        logging.info("To be processed: " + str(submission.url))


    for submission in to_be_done:
        if (str(submission.id), ) in curs.execute("SELECT ID FROM reddit"):
            logging.info("Already processed submission " + str(submission.id))
            continue
        else:
            try:
                media_id = get_media_id.get_media_id(str(submission.url)).encode('utf-8').strip()
                this_media = api.media(media_id)

                media_type = this_media.type.encode('utf-8').capitalize()
                formatted_comment = comments.comment.format(media_type)

                author_full_name = this_media.user.full_name.encode('utf-8')
                author_name = this_media.user.username.encode('utf-8')
                author_url = "http://www.instagram.com/%s" % author_name
                post_url = this_media.link.encode('utf-8')
                post_date = this_media.created_time.strftime("%Y-%m-%d %H:%M:%S")
                caption = escape.escape_chars(this_media.caption.text.encode('utf-8')) if this_media.caption.text != None else ""
                media_url = this_media.images['standard_resolution'].url.encode('utf-8') if media_type == "Image" else this_media.videos['standard_resolution'].url.encode('utf-8')
                rehosted_url = rehost.rehost(media_url)

                try:
                    curs.execute("INSERT INTO reddit (ID, TIMESTAMP) VALUES (?, CURRENT_TIMESTAMP)",(str(submission.id),))
                    logging.debug("Succesfully added submission " + str(submission.id) + " to the database")
                    db.commit()
                    logging.debug("Successfully committed submission " + str(submission.id) + " to the database")
                except sqlite3.Error as e:
                    logging.critical("Unable to add submission: " + str(submission.id) + " to the database because of : " + str(e))
                    continue

                try:
                    final_comment = formatted_comment % (author_full_name, author_name, author_url, post_url, post_date, caption, media_url, rehosted_url)
                    post = submission.add_comment(final_comment)
                    r.get_info(thing_id="t1_"+str(post.id)).edit(final_comment.replace("__id__", str(post.id)))
                    logging.debug("Successfully submitted comment for submission: " + str(submission.id))
                except praw.errors.APIException as e:
                    logging.critical("Comment submission for "+ str(submission.id) + " not processed because " + str(e))
                    continue

                logging.info("Succesfully processed and posted comment at " + "http://www.reddit.com/" + str(submission.id))
            except ValueError as e:
                logging.critical("Not proccessed because of this error: " + str(e) + ". Line number: " + str(sys.exc_info()[-1].tb_lineno))
            except InstagramAPIError as e:
                logging.critical("Not proccessed because of this error: " + str(e) + ". Line number: " + str(sys.exc_info()[-1].tb_lineno))
            except Exception as e:
                logging.critical("Not proccessed because of this error: " + str(e) + ". Line number: " + str(sys.exc_info()[-1].tb_lineno))
        logging.info("Sleeping for 10 secs")
        time.sleep(10)
    db.commit()
    logging.info("Sleeping for 15 mins")
    time.sleep(900)
