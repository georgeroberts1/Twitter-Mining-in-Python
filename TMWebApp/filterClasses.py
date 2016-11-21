import string
import operator
import vincent
import pandas
import math

from tokeniser import preprocess
from nltk.corpus import stopwords
from nltk import bigrams
from collections import defaultdict

class termCount(object):

    def __init__(self, tweet, word, com, count_search):
        self.tweet = tweet

        # Create a list with all the terms
        self.terms_all = [term for term in preprocess(tweet['text'])]

        punctuation = list(string.punctuation)
        stop = stopwords.words('english') + punctuation + ['rt', 'RT', 'via']
        # Create a list with all the terms removing stop words
        self.terms_stop = [term for term in preprocess(tweet['text']) if term not in stop]

        # Count terms only once, equivalent to Document Frequency
        self.terms_single = set(self.terms_all)

        # Count hashtags only
        self.terms_hash = [term for term in preprocess(tweet['text'])
                      if term.startswith('#')]

        # Count terms only (no hashtags, no mentions)
        self.terms_only = [term for term in preprocess(tweet['text'])
                      if term not in stop and
                      not term.startswith(('#', '@'))]
        # mind the ((double brackets))
        # startswith() takes a tuple (not a list) if
        # we pass a list of inputs

        # Count most frequently occurring adjacent terms (as tuples)
        self.terms_bigram = bigrams(self.terms_stop)

        # Count most frequent co-occurrences:
        # We build a co-occurrence matrix com such that com[x][y] contains the number of times the term x
        # has been seen in the same tweet as the term y

        self.com = com
        for i in range(len(self.terms_only) - 1):
            for j in range(i + 1, len(self.terms_only)):
                w1, w2 = sorted([self.terms_only[i], self.terms_only[j]])
                if w1 != w2:
                    com[w1][w2] += 1

        com_max = []
        # For each term, look for the most common co-occurrent terms
        for t1 in com:
            t1_max_terms = sorted(com[t1].items(), key=operator.itemgetter(1), reverse=True)[:5]
            for t2, t2_count in t1_max_terms:
                com_max.append(((t1, t2), t2_count))
        # Get the most frequent co-occurrences
        terms_max_unranked = sorted(com_max, key=operator.itemgetter(1), reverse=True)
        self.terms_max = terms_max_unranked

        self.search_word = word
        self.count_search = count_search

    def search_cooccurrences(self):
        termFilter = self.terms_stop
        if self.search_word in termFilter:
            self.count_search.update(termFilter)

class counted_data_plot(object):

    def __init__(self, count_terms_choice):
        self.count_choice = count_terms_choice

    def counted_data(self):
        word_freq = self.count_choice
        labels, freq = zip(*word_freq)
        data = {'data': freq, 'x': labels}
        bar = vincent.Bar(data, iter_idx='x')
        bar.width = 2000
        bar.to_json('term_freq.json')

class time_data_build(object):

    def __init__(self, tweet, terms_choice, search_string, date_array):
        self.tweet = tweet
        self.terms_choice = terms_choice
        self.search_string = search_string
        self.date_array = date_array

    def append_dates(self):

        if self.search_string in self.terms_choice:
            self.date_array.append(self.tweet['created_at'])

class time_data_plot(object):

    def __init__(self, date_array, date_array_2):
        self.date_array = date_array
        self.date_array_2 = date_array_2

    def plot_series(self):
        # a list of "1" to count the hashtags
        ones = [1] * len(self.date_array)
        # the index of the series
        idx = pandas.DatetimeIndex(self.date_array)
        # the actual series (at series of 1s for the moment)
        first_term = pandas.Series(ones, index=idx)
        # Resampling / bucketing
        per_second = first_term.resample('1S').sum().fillna(0)

        time_chart = vincent.Line(per_second)
        time_chart.axis_titles(x='Time', y='Freq')
        time_chart.width = 1000
        time_chart.to_json('time_chart.json')

    def plot_two_series(self):
        date_array_1 = self.date_array
        ones = [1] * len(date_array_1)
        idx_1 = pandas.DatetimeIndex(date_array_1)
        first_term = pandas.Series(ones, index=idx_1)
        per_second_1 = first_term.resample('1S').sum().fillna(0)

        ones = [1] * len(self.date_array_2)
        idx_2 = pandas.DatetimeIndex(self.date_array_2)
        first_term = pandas.Series(ones, index=idx_2)
        per_second_2 = first_term.resample('1S').sum().fillna(0)

        # all the data together
        match_data = dict(term1=per_second_1, term2=per_second_2)
        # we need a DataFrame, to accommodate multiple series
        all_matches = pandas.DataFrame(data=match_data,
                                       index=per_second_1.index)
        # Resampling as above
        all_matches = all_matches.resample('1S').sum().fillna(0)

        # and now the plotting
        time_chart = vincent.Line(all_matches[['term1', 'term2']])
        time_chart.axis_titles(x='Time', y='Freq')
        time_chart.legend(title='Matches')
        time_chart.width = 1000
        time_chart.to_json('time_chart.json')

class semantics(object):

    def __init__(self, count_stop_single, num_Tweets, com):
        # n_docs is the total n. of tweets
        self.p_t = {}
        self.p_t_com = defaultdict(lambda: defaultdict(int))
        self.count_stop_single = count_stop_single
        self.positive_vocab = [
            'good', 'nice', 'great', 'awesome', 'outstanding',
            'fantastic', 'terrific', ':)', ':-)', 'like', 'love',
            # shall we also include game-specific terms?
            # 'triumph', 'triumphal', 'triumphant', 'victory', etc.
        ]
        self.negative_vocab = [
            'bad', 'terrible', 'crap', 'useless', 'hate', ':(', ':-(',
            # 'defeat', etc.
        ]
        self.num_Tweets = float(num_Tweets)
        self.top_pos = None
        self.top_neg = None
        self.com = com
        self.s_o = {}

    def semantic_orientation(self):

        for term, n in self.count_stop_single.items():
            self.p_t[term] = n / self.num_Tweets
            for t2 in self.com[term]:
                self.p_t_com[term][t2] = self.com[term][t2] / self.num_Tweets

        pmi = defaultdict(lambda: defaultdict(int))
        for t1 in self.p_t:
            for t2 in self.com[t1]:
                denom = self.p_t[t1] * self.p_t[t2]
                pmi[t1][t2] = math.log(self.p_t_com[t1][t2] / denom)

        for term, n in self.p_t.items():
            positive_assoc = sum(pmi[term][tx] for tx in self.positive_vocab)
            negative_assoc = sum(pmi[term][tx] for tx in self.negative_vocab)
            self.s_o[term] = positive_assoc - negative_assoc

        semantic_sorted = sorted(self.s_o.items(),
                                 key=operator.itemgetter(1),
                                 reverse=True)
        self.top_pos = semantic_sorted[:10]
        self.top_neg = semantic_sorted[-10:]

