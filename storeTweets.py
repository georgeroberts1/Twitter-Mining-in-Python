import tweepy
import psycopg2
import json
import sys
from tweepy import OAuthHandler

try:
    conn = psycopg2.connect("dbname='TwitterMining' user='postgres' host='localhost' password='dbpass'")
    print "Connected to database...\n"

    consumer_key = 'XD6e7m8dlDVRCl2HqtzWnI11R'
    consumer_secret = 'rg3DzAbWRuqrSCx5Yad3JR7LmS2TZh6DxkZhw2XTtk7nY03ivz'
    access_token = '3378013539-tlWHoSU3cJzSE2kwl7PFuplAlyBRQ7zVyQe5tkR'
    access_secret = 'aBz3GCr9bzv787qEPBg9wCA9ILgebUn47MpgJ8BpuEYb9'

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


