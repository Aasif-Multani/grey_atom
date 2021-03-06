#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Aasif Multani"

"""
Commonutils.py module is used to define functions
whch are required to execute at the time of server
inialisation.
"""

# Headers
import json
from demjson import decode
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import os.path


class Commonutils(object):

    def cleanJson(filename):
        """
        Function used to convert the Q&A dataset to a Json file
        Input : Path of the dataset
        Output : Json file
        """
        saveFile = 'newFile.json'

        # check if file exists and exit if it does
        if os.path.exists(saveFile):
            return

        with open(filename) as f:
            contents = f.readlines()

        with open('newFile.json', 'a') as outfile:
            for line in contents:
                # convert line from JSON to Python dictionary
                dic = decode(line)
                # convert dic to a string representing a json object
                json_obj = json.dumps(dic)
                outfile.write(json_obj)  # write to outfile
                outfile.write("\n")

    def sentiments(dataframe, flag):
        """
        Function used to calculate the sentimets
        Input : Data frame and flag
        Output : Positive and negative sentiments
        """
        analyser = SentimentIntensityAnalyzer()

        if flag == 'q':
            list1 = []
            column = dataframe['answer']
            for i in column:
                sent = analyser.polarity_scores(i)
                list1.append(sent['compound'])
            qa_sentiments = ['positive' if i >= 0 else 'negative' for i in list1]
            return qa_sentiments
        elif flag == 'r':
            list2 = []
            column = dataframe['reviewText']
            for i in column:
                sent = analyser.polarity_scores(i)
                list2.append(sent['compound'])
            temp = [1 if i >= 0 else 0 for i in list2]
            # verify sentiment against the
            # overall product ratings
            list3 = []
            for i in range(len(dataframe)):
                list3.append(dataframe['overall'][i] + temp[i])
            review_sentiments = ['positive' if i >= 3 else 'negative' for i in list3]
            return review_sentiments

    def load_reveiws_dataset(filename):
        """
        Functions used to load reveiw dataset
        Input : Path of the dataset
        Output : Data frame
        """
        review_DataFrame = pd.read_json(filename, lines=True)
        return review_DataFrame

    def remove_unhelpful_reviews(reviewDF, threshold=0.5):
        """
        Function used to remove unhelpful reviews from review dataset
        Input : Review dataset and threshold for helpfulness
        Output : Review dataset with only helpful reviews
        """
        rv = reviewDF.sort_values(by='helpful')  # save sorted original dataframe
        helpful = list(rv['helpful'])  # take the helpful column values into a list
        list1 = [item[0] for item in helpful]  # take first element into list1
        list2 = [item[1] for item in helpful]  # take second element into list2
        rv['foundHelpful'] = list1  # add a column out of list1
        rv['totalVoters'] = list2  # add a column out of list2

        # Trials showed that the avg user vote per rating was very low when all
        # votes were considered. Hence we took only unique set of ratings.
        uniqueVotes = [list(x) for x in set(tuple(x) for x in helpful)]
        list3 = [item[0] for item in uniqueVotes]  # take first element into list3
        list4 = [item[1] for item in uniqueVotes]  # take second element into list4
        # create a dataframe out of it
        tempDf = pd.DataFrame({'uniqueFoundHelpful': list3, 'uniqueTotalVoters': list4})
        # find the average of total voter per rating
        tempDf = tempDf.groupby(by='uniqueFoundHelpful').mean()

        avg = tempDf['uniqueTotalVoters']
        inplace = list(tempDf.index)
        # take the percentage of average based on the given threshold
        avg_Percent = [round(i * threshold) for i in avg]

        # map the avg_Percentage value wrt the rating
        # CAUTION !!! VERY SLOW!
        list4 = []
        pos = 0
        for i in inplace:
            for j in range(len(rv['foundHelpful'])):
                if i == rv['foundHelpful'][j]:
                    list4.append(avg_Percent[pos])
            pos += 1

        rv['cap'] = list4  # place the mapped list into rv and call it 'cap'
        # sort the index, because mapping was done based on value
        rv = rv.sort_index()

        # mark helpfulness based on the difference in the
        # totalVoters and the ones who found it helpful and compare it with
        # the cap to find if it is helpful or not!
        # 1 = helpful, 0 = nothelpful.
        helpfulness = 0
        helplist = []
        for i in range(len(rv)):
            diff = rv['totalVoters'][i] - rv['foundHelpful'][i]
            cap = rv['cap'][i]
            if diff <= cap:
                helpfulness = 1
            else:
                helpfulness = 0
            helplist.append(helpfulness)

        rv['helpfulness'] = helplist

        # drop all non helpful reviews
        nrv = rv.drop(rv[rv.helpfulness == 0].index)
        # drop all extra columns
        nrv = nrv.drop(['foundHelpful', 'totalVoters', 'cap', 'helpfulness'], axis=1)
        # return cleaned dataframe
        return nrv
