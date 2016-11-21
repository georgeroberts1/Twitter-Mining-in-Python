import psycopg2
import json
import sys
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

try:
    conn = psycopg2.connect("dbname='TwitterMining' user='postgres' host='localhost' password='dbpass'")
    print "Connected to database...\n"

    consumer_key = 'enter consumer_key'
    consumer_secret = 'enter consumer_secret'
    access_token = 'enter access_token'
    access_secret = 'enter access_secret'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE uselection6")
    limit = 50000

    class MyListener(StreamListener):
        def __init__(self, api=None):
            super(MyListener, self).__init__()
            self.num_tweets = 0

        def on_status(self, status):
            dictionary = json.dumps(status._json)
            self.num_tweets += 1
            if self.num_tweets <= limit:
                cur.execute("INSERT INTO uselection6 (json) VALUES (%s)", (dictionary,))
                conn.commit()
                # print dictionary
                print '%s uselection6 added' % self.num_tweets
                return True
            else:
                return False

        def on_error(self, status):
            print status

    twitterStream = Stream(auth, MyListener())
    twitterStream.filter(track=['#ElectionDay'])

except psycopg2.DatabaseError, e:

    if conn:
        conn.rollback()

    print 'Error %s' % e

    sys.exit(1)


finally:

    if conn:
        conn.close()