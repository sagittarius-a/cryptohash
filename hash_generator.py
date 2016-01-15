#!/usr/bin/python2
# coding: utf-8

# Don't forget the: pip install docopt
# Don't forget the: pip install redis
# Don't forget the: pip install pymongo

"""
    Hash_generator v0.1 - November, 18th 2015

        "Hash it to the limits" - Genier Emmanuel

    Usage:
        hash_generator.py (-f | --file) <PASSWORD_FILE> (-t | --type) <type> [-d | --debug] [-s | --substitutions]
        hash_generator.py (hash <password>) [-t | --type <type>] [-d | --debug] [-s | --substitutions]
        hash_generator.py [(-f | --file) <PASSWORD_FILE>]
        hash_generator.py (-h | --help)
        hash_generator.py (-v | --version)

    Options:
        -f --file           Specifies the file containing passwords to hash
        -t --type           Specifies the database type
        -d --debug          Enable verbose output
        -h --help           Show this screen.
        -v --version        Show version.

"""

from docopt import docopt
from pymongo import MongoClient
import hashlib
import redis
import sys

"""

    Script generating hashes from a password (list) and storing them in
    a mongodb or a redis database.

    ex:
    python2 hash_generator.py -f password.txt -t redis -d
    python2 hash_generator.py -f worst_pass.txt -t mongo

    To search a row in the db (mongo):
    > db.rainbow.find({"hashed": "49d02d55ad10973b7b9d0dc9eba7fdf0"})
    or
    > db.rainbow.find({"plain": "123456"})

"""


def hashittothelimit(password, db_connector=None, type=None, substitutions=False, debug=False):
    """Hash a password and store it in a database."""
    # Using all available algorithm and removing duplicate entries
    # available_hashes = ["MDC2", "MD4", "MD5", "RIPEMD160", "DSA", "SHA",
                        # "SHA1", "SHA256", "SHA384", "SHA512",  "whirlpool"]

    available_hashes = list(hashlib.algorithms_guaranteed)            

    if SUB:
        substitutions = find_substitutions(password)
    else:
        substitutions = []
        substitutions.append(password)

    for sub in substitutions:
        if debug:
            print "\n[!] Hashing '" + sub + "':"
        for hash in available_hashes:
            # if hash is in hashlib.algorithms:
            h = hashlib.new(hash)
            h.update(sub)
            hashed = h.hexdigest()

            if debug:
                print "[+]", '{:>15}:'.format(hash), sub, "->", hashed

            # Insert it in the appropriate database
            if type == "mongo":
                mongo_store(db_connector, hashed, sub)
            elif type == "redis":
                redis_store(db_connector, hashed, sub)


def find_substitutions(password):
    """Compute few common substitutions for a password."""
    subs = []

    subs.append(password.upper())
    if "a" in password:
        subs.append(password.replace("a", "@"))

    # Leet substitutions
    leet = {"i": "1", "l": "1",
            "e": "3",
            "a": "4",
            "s": "5",
            "b": "6",
            "t": "7",
            "g": "9",
            "o": "0"}
    for key, value in leet.items():
        if key in password:
            subs.append(password.lower().replace(key, value))
    # Add a character at the end
    for e in ["!", "?", "/", "%", "+", "-", "#"]:
        subs.append(password+e)
    # Add a number at the end, from 1 to 9
    for i in xrange(0, 10):
        subs.append(password+str(i))

    return subs


def redis_store(db_connector, hashed_password, plain_text_password):
    """Store a password in a redis instance."""
    db_connector.hset("rainbow", hashed_password, plain_text_password)
    return 0


def mongo_store(db_connector, hashed_password, plain_text_password):
    """Store a password in a mongo instance."""
    db_connector.rainbow.insert_one(
        {
            "hashed": hashed_password,
            "plain": plain_text_password
        }
    )
    return 0


# Script ----------------------------------------------------------------------
if __name__ == '__main__':
    # Setting up docopt
    arguments = docopt(__doc__, version="Hash_generator v0.1")
    # print arguments

    DEBUG = False
    if arguments.get("--debug") or arguments.get("-d"):
        DEBUG = True

    SUB = False
    if arguments.get("--substitutions") or arguments.get("-s"):
        SUB = True

    # DATABASE ----------------------------------------------------------------
    # Parsing arguments to find the database type and setting the connector
    DB = None
    TYPE = None
    try:
        if arguments.get("<type>") == "mongo":
            client = MongoClient("mongodb://127.0.0.1:27017")
            DB = client.test
            TYPE = "mongo"
        if arguments.get("<type>") == "redis":
            DB = redis.Redis('localhost')
            TYPE = "redis"
    except Exception as e:
        print "Error opening database : %s.\nQuitting." % e
        raise

    print ">>> TYPE", TYPE, "DEBUG", DEBUG, "SUB", SUB, "<<<"

    # ONESHOT -----------------------------------------------------------------
    # If the user wants to hash a unique password
    if arguments.get("hash"):
        password = arguments.get("<password>")
        print "Hashing only: %s." % password
        hashittothelimit(password, DB, TYPE, SUB, DEBUG)
        print "Goodbye."
        sys.exit(0)

    # PASSWORDS SOURCE --------------------------------------------------------
    # If the user wants to parse a password file
    if arguments.get("--file") or arguments.get("-f"):
        file = arguments.get("<PASSWORD_FILE>")
        print "reading file %s" % file
        # Try to open the file and hash every password
        try:
            with open(file, 'r') as f:
                for passwd in f:
                    hashittothelimit(passwd.strip(), DB, TYPE, SUB, DEBUG)
            print "Goodbye."
            sys.exit(0)
        except Exception, e:
            print "Error opening file : %s" % e
    # If no valid arguments are used, help the user
    else:
        print __doc__
