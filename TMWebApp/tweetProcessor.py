import json

from collections import Counter
from collections import defaultdict
from filterClasses import termCount
from filterClasses import counted_data_plot
from filterClasses import time_data_build
from filterClasses import time_data_plot
from filterClasses import semantics

fname = 'tweets.json'

with open(fname, 'r') as f:
    count_all = Counter()
    count_search = Counter()
    count_terms_choice = Counter()
    count_stop_single = Counter()

    dates_first_term = []
    dates_second_term = []
    search_term1 = "Trump"
    search_term2 = "like"
    search_string = "#Trump"
    num_Tweets = 0
    com = defaultdict(lambda: defaultdict(int))

    for line in f:
        tweet = json.loads(line)
        filterTweet = termCount(tweet, search_string, com, count_search)
        tweet_time = time_data_build(tweet, filterTweet.terms_stop, search_string=search_term1, date_array=dates_first_term)
        tweet_time_2 = time_data_build(tweet, filterTweet.terms_stop, search_string=search_term2, date_array=dates_second_term)

        # Update the counter
        count_all.update(filterTweet.terms_stop)
        filterTweet.search_cooccurrences()
        count_terms_choice.update(filterTweet.terms_hash)
        tweet_time.append_dates()
        tweet_time_2.append_dates()
        count_stop_single.update(filterTweet.terms_stop)
        num_Tweets = num_Tweets + 1
    print(count_stop_single.most_common(20))
    print "\n"

    # counted_data_plot(count_terms_choice.most_common(20)).counted_data()
    # time_data_plot(dates_first_term, dates_second_term).plot_two_series()
    semantic_instance = semantics(count_stop_single, num_Tweets, com)
    semantic_instance.semantic_orientation()

    print(semantic_instance.top_pos)
    print(semantic_instance.top_neg)

    search_term = 'less'
    print("%s: %f" % (search_term, semantic_instance.s_o[search_term]))

