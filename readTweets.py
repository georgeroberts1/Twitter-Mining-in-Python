import psycopg2
import sys
import json
import string
import operator
import vincent
import pandas
import numpy as np
from collections import Counter
from processTweets import preprocess
from processTweets import positive_vocab
from processTweets import negative_vocab
from nltk.corpus import stopwords
from nltk import bigrams
from collections import defaultdict

try:
    conn = psycopg2.connect("dbname='TwitterMining' user='postgres' host='localhost' password='dbpass'")

    cur = conn.cursor()
    cur.execute("SELECT * FROM uselection6")

    rows = cur.fetchall()

    dates_trump = []
    dates_hillary = []
    count = 0

    count_all = Counter()

    count_stop_single = Counter()

    com = defaultdict(lambda: defaultdict(int))

    geo_data = {
        "type": "FeatureCollection",
        "features": []
    }

    for row in rows:

        line = row[0]  # read only the first tweet/line
        tweet = json.loads(line)  # load it as Python dict
        punctuation = list(string.punctuation)

        # Create a list with all the terms
        terms_all = [term for term in preprocess(tweet['text'])]

        stop = stopwords.words('english') + punctuation + ['RT', 'via']
        terms_stop = [term for term in preprocess(tweet['text']) if term not in stop]

        # Count most common two adjacent terms
        terms_bigram = bigrams(terms_stop)

        # Count terms only once, equivalent to Document Frequency
        terms_single = set(terms_all)

        # Count hashtags only
        terms_hash = [term for term in preprocess(tweet['text'])
                      if term.startswith('#')]

        # track when the hashtag is mentioned
        if '#trump' in terms_hash:
            dates_trump.append(tweet['created_at'])

        if '#hillary' in terms_hash:
            dates_hillary.append(tweet['created_at'])

        # Count terms only (no hashtags, no mentions)
        terms_only = [term for term in preprocess(tweet['text'])
              if term not in stop and
              not term.startswith(('#', '@'))]
        # mind the ((double brackets))
        # startswith() takes a tuple (not a list) if
        # we pass a list of inputs

        # Count co-occurring terms (two terms that appear in the same tweet) by building a co-occurrence matrix
        for i in range(len(terms_only) - 1):
            for j in range(i + 1, len(terms_only)):
                w1, w2 = sorted([terms_only[i], terms_only[j]])
                if w1 != w2:
                    com[w1][w2] += 1

        # com_max = []
        # # For each term, look for the most common co-occurrent terms
        # for t1 in com:
        #     t1_max_terms = sorted(com[t1].items(), key=operator.itemgetter(1), reverse=True)[:5]
        #     for t2, t2_count in t1_max_terms:
        #         com_max.append(((t1, t2), t2_count))

        # Get the most frequent co-occurrences
        # terms_max = sorted(com_max, key=operator.itemgetter(1), reverse=True)
        # to output e.g. print(terms_max[:5]) - 5 being the top co-occurrent term pairs in each tweet

        # Count the most frequent co-occurrences for a single specific term
        # search_word = 'trump'  # pass a term as a command-line argument
        # if search_word in terms_only:
        #     count_all.update(terms_only)

        # Standard Count
        # count_all.update(terms_stop)

        # Semantics Analysis Count
        count_stop_single.update(terms_stop)

        if tweet['coordinates']:
            geo_json_feature = {
                "type": "Feature",
                "geometry": tweet['coordinates'],
                "properties": {
                    "text": tweet['text'],
                    "created_at": tweet['created_at']
                }
            }
            geo_data['features'].append(geo_json_feature)

    # Save geo data
    with open('geo_data.json', 'w') as fout:
        fout.write(json.dumps(geo_data, indent=4))

    # Standard print
    print(count_stop_single.most_common(10))

    # # Create visuals of given data
    # word_freq = count_stop_single.most_common(20)
    # labels, freq = zip(*word_freq)
    # data = {'data': freq, 'x': labels}
    # bar = vincent.Bar(data, iter_idx='x')
    # bar.to_json('term_freq.json')
    #
    # # Create visuals of time related data
    # # a list of "1" to count the hashtags
    # onesT = [1] * len(dates_trump)
    # onesH = [1] * len(dates_hillary)
    # # the index of the series
    # idxT = pandas.DatetimeIndex(dates_trump)
    # idxH = pandas.DatetimeIndex(dates_hillary)
    # # the actual series (at series of 1s for the moment)
    # trump = pandas.Series(onesT, index=idxT)
    # hillary = pandas.Series(onesH, index=idxH)
    # # Resampling / bucketing
    # per_seconds_t = trump.resample('1S').sum().fillna(0)
    # per_seconds_h = hillary.resample('1S').sum().fillna(0)

    # FOR tracking a single term
    # time_chart = vincent.Line(per_resampleTime)
    # time_chart.axis_titles(x='Time', y='Freq')
    # time_chart.to_json('time_chart.json')

    # Create visuals tracking > 1 term
    # all the data together
    # match_data = dict(Trump=per_seconds_t, Hillary=per_seconds_h)
    # we need a DataFrame, to accommodate multiple series
    # all_matches = pandas.DataFrame(data=match_data,
    #                                index=per_seconds_t.index)
    # Resampling as above
    # all_matches = all_matches.resample('1S').sum().fillna(0)

    # and now the plotting
    # time_chart = vincent.Line(all_matches[['Trump', 'Hillary']])
    # time_chart.axis_titles(x='Time', y='Freq')
    # time_chart.legend(title='Matches')
    # time_chart.to_json('time_chart.json')

    # Sentiment Analysis
    n_docs = float(50000)
    p_t = {}
    p_t_com = defaultdict(lambda: defaultdict(int))

    for term, n in count_stop_single.items():
        p_t[term] = n / n_docs

        for t2 in com[term]:
            p_t_com[term][t2] = com[term][t2] / n_docs

    pmi = defaultdict(lambda: defaultdict(int))
    for t1 in p_t:
        for t2 in com[t1]:
            denom = p_t[t1] * p_t[t2]
            pmi[t1][t2] = np.log2(p_t_com[t1][t2] / denom)

    semantic_orientation = {}
    for term, n in p_t.items():
        positive_assoc = sum(pmi[term][tx] for tx in positive_vocab)
        negative_assoc = sum(pmi[term][tx] for tx in negative_vocab)
        semantic_orientation[term] = positive_assoc - negative_assoc

    semantic_sorted = sorted(semantic_orientation.items(),
                             key=operator.itemgetter(1),
                             reverse=True)
    top_pos = semantic_sorted[:2]
    top_neg = semantic_sorted[-2:]

    print(top_pos)
    print(top_neg)
    print("Donald: %f" % semantic_orientation['Donald'])
    print("Trump: %f" % semantic_orientation['Trump'])
    print("GOP: %f" % semantic_orientation['GOP'])
    print("Hillary: %f" % semantic_orientation['Hillary'])
    print("Clinton: %f" % semantic_orientation['Clinton'])
    print("democrat: %f" % semantic_orientation['democrat'])

except psycopg2.DatabaseError, e:
    print 'Error %s' % e
    sys.exit(1)

finally:
    if conn:
        conn.close()