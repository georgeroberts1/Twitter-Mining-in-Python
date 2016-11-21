import time
import authentication

from tweepy import Stream
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler

auth = OAuthHandler(authentication.consumer_key, authentication.consumer_secret)
auth.set_access_token(authentication.access_token, authentication.access_secret)

class MyListener(StreamListener):
    """Custom StreamListener for streaming data."""

    def __init__(self, time_limit):
        self.outfile = "tweets.json"
        self.start_time = time.time()
        self.limit = time_limit

    def on_data(self, data):
        try:
            with open(self.outfile, 'a') as f:
                if (time.time() - self.start_time) < self.limit:
                    f.write(data)
                    print "tweets added"
                    return True
                else:
                    f.close()
                    print "tweets.json has been saved \n %s second time limit has been reached" % self.limit
                    return False

        except BaseException as e:
            print("Error on_data: %s" % str(e))
            time.sleep(5)
        return True

    def on_error(self, status):
        print(status)
        return True

twitter_stream = Stream(auth, MyListener(100))
twitter_stream.filter(track=['#trump'])
twitter_stream.disconnect()