import tweepy
import psycopg2
import json
import sys
from tweepy import OAuthHandler

try:
    conn = psycopg2.connect("dbname='TwitterMining' user='postgres' host='localhost' password='dbpass'")
    print "Connected to database...\n"

    consumer_key = 'enter consumer_key'
    consumer_secret = 'enter consumer_secret'
    access_token = 'enter access_token'
    access_secret = 'enter access_secret'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)

    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE tweets1")
    numTweets = 100

    for status in tweepy.Cursor(api.home_timeline).items(numTweets):
        # dictionary = status._json

        dictionary = json.dumps(status._json)

        cur.execute("INSERT INTO tweets1 (json) VALUES (%s)", (dictionary,))
        # print (dictionary)

    conn.commit()

    print '%s tweets have been stored' % numTweets


except psycopg2.DatabaseError, e:

    if conn:
        conn.rollback()

    print 'Error %s' % e

    sys.exit(1)


finally:

    if conn:
        conn.close()


