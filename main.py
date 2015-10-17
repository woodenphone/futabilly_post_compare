#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     15/10/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import logging
import re
import os
import json
import sqlalchemy# Database library

import config # Settings and configuration
import lockfiles # MutEx lockfiles
from utils import * # General utility functions
import sql_functions# Database interaction
from tables import Board# Table definitions


def unfuck_futabully_json(bad_json):
    """
    Convert what we're given to something we can use.
    OdiliTime> Sorry I should have never called it json, I confuse myself cause its close
    """
    # Prepend "["
    less_bad_json = "["+bad_json
    # Remove trailing ",\n"
    less_bad_json = less_bad_json[:-2]
    # Append "]"
    less_bad_json = less_bad_json+"]"
    return less_bad_json


def compare_thread(thread_a,thread_b):
    """
    Compare two threads
    Expected format:
        [{u'2': [3439657, 1443320691],
          u'c': u"http://theantimedia.org/tpp-negotiators-meeting-this-week-to-finalize-corporate-trade-deal/?utm_source=SocialWarfare&amp;utm_medium=facebook&amp;utm_campaign=SocialWarfare\nI can't help but think the speaker of the house stepped down because of the backlash he knew he was going to endure from this bill. Obongo, though, as an ape probably didn't consider it just yet.\n\nThis shit is happening, and it better not pass unless congress wants to deal with a fucking hell of an angry country after them.",
          u'f': 1,
          u'm': [u'data/media/_global/AQ/lhAft6y34XNJSm2sTDcj4i+p3aJmMwvgZzdRT3MN7JGImt+7z26cczJWO6+kLuPGV1ZPNprFc2tMTWxuZwWJAQ.jpg']},
         {u'2': [3439690, 1443320995], u'c': u'Bump, niggers.'},
         {u'2': [3439748, 1443321493],
          u'c': u">mfw I see this\n\nIt's all going to be ogre soon.",
          u'm': [u'lhAft6y34XNJSm2sTDcj4i+p3aJmMwvgZzdRT3MN7JGImt+7z26cczJWO6+kLuPGV1ZPNprFc2tMTWxuZwWJAQ.jpg']},
         {u'2': [3440085, 1443325396],
          u'c': u"I'll bump this thread for you, OP. TPP is always relevant."},
         {u'2': [3440107, 1443325610],
          u'c': u">>3440085\n\n>\u201cWithin the Republican Party, some of the same impulses that are anti-immigration reform, some of the same impulses that see the entire world as a threat, and we\u2019ve got to wall ourselves off, some of those same impulses start creeping into the trade debate, and a party that was traditionally pro-free trade now has a substantial element that may feel differently,\u201d Obama stated.\n\nSlightly off topic but didn't the GOP originally support tariffs and restrictive trade policies at one point (Old Right)? Or am I mixed up?"},
         {u'2': [3440118, 1443325693], u'c': u'>>3440085\n\nThanks, son.'},
         ...
        ]
    List of post dicts
    """
    posts_matched = True
    # Check that both have the same posts
    thread_a_post_ids = []
    for thread_a_post in thread_a:
        thread_a_post_ids += [thread_a_post["2"][0]]

    thread_a_post_ids = []
    for thread_a_post in thread_a:
        thread_a_post_ids += [thread_a_post["2"][0]]

    post_counts_matched = (len(thread_a_post_ids) == len(thread_a_post_ids))# Both should have the same number of posts
    logging.debug("post_counts_matched: "+repr(post_counts_matched))


    # Convert to dicts using postid as key to make comparisons faster
    thread_a_posts = {}
    for thread_a_post in thread_a:
        post_id = thread_a_post["2"][0]
        thread_a_posts[post_id] = thread_a_post

    thread_b_posts = {}
    for thread_b_post in thread_b:
        post_id = thread_b_post["2"][0]
        thread_b_posts[post_id] = thread_b_post

    # Check that each post is identical to one in the other thread
    for post_id in thread_a_posts.keys():
        thread_a_post = thread_a_posts[post_id]
        thread_b_post = thread_b_posts[post_id]

        # Times thould match
        post_times_matched = (thread_a_post["2"][1] == thread_b_post["2"][1])
        logging.debug("post_times_matched: "+repr(post_times_matched))
        if not post_times_matched:
            posts_matched = False

        # Comments should match
        comment_matched = (thread_a_post["c"] == thread_b_post["c"])
        logging.debug("comment_matched: "+repr(comment_matched))
        if not comment_matched:
            posts_matched = False

        # File hashes
        if (
            ("m" in thread_a_post.keys()) or
            ("m" in thread_b_post.keys())
            ):
            # Both posts should have the same number of file hashes
            hash_counts_matched = ( len(thread_a_post["m"]) == len(thread_b_post["m"]) )
            logging.debug("hash_counts_matched: "+repr(hash_counts_matched))
            if not hash_counts_matched:
                posts_matched = False

            # File hashes should match
            for thread_a_file_hash in thread_a_post["m"]:
                hash_matched = (thread_a_file_hash in thread_b_post["m"])
                logging.debug("hash_matched: "+repr(hash_matched))
                if not hash_matched:
                    posts_matched = False

        # Names should match if they exist
        if (
            ("n" in thread_a_post.keys()) or
            ("n" in thread_b_post.keys())
            ):
            names_matched = (thread_a_post["n"] == thread_b_post["n"])
            logging.debug("names_matched: "+repr(names_matched))
            if not names_matched:
                posts_matched = False

    return posts_matched


def test_match():
    # Load thread a
    original_thread_a_json = read_file(os.path.join("example_threads", "match", "3439657_.json"))
    cleaned_thread_a_json = unfuck_futabully_json(bad_json=original_thread_a_json)
    thread_a = json.loads(cleaned_thread_a_json)
    #logging.debug("thread_a: "+repr(thread_a))
    # Load thread b
    thread_b_json = read_file(os.path.join("example_threads", "match", "cleaned_3439657_.json"))
    thread_b = json.loads(thread_b_json)
    #logging.debug("thread_b: "+repr(thread_b))
    # Comapare a and b
    threads_matched = compare_thread(thread_a,thread_b)
    logging.info("threads_matched: "+repr(threads_matched))
    assert(threads_matched)
    return


def test_mismatch():
    # Load thread a
    original_thread_a_json = read_file(os.path.join("example_threads", "mismatch", "3439657_.json"))
    cleaned_thread_a_json = unfuck_futabully_json(bad_json=original_thread_a_json)
    thread_a = json.loads(cleaned_thread_a_json)
    #logging.debug("thread_a: "+repr(thread_a))
    # Load thread b
    thread_b_json = read_file(os.path.join("example_threads", "mismatch", "cleaned_3439657_.json"))
    thread_b = json.loads(thread_b_json)
    #logging.debug("thread_b: "+repr(thread_b))
    # Comapare a and b
    threads_matched = compare_thread(thread_a,thread_b)
    logging.info("threads_matched: "+repr(threads_matched))
    assert( not threads_matched )
    return


def debug():
    """where stuff is called to debug and test"""
    test_match()
    test_mismatch()


    return



def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","futabilly_thread_compare-log.txt"))

        debug()

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
