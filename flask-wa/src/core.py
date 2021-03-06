#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module contains a class that will be spawned by the webapp
to process the input and return the results"""

__author__ = "Aasif Multani"

from queryhandler import QueryHandler
from relevancecheck import RelevanceCheck
import pandas as pd


class Core():
    """Implementation of core functions to handle user query
    from webapp and return relevant results.

    Attributes
    ----------
    query : string
        User query recieved as a json string converted to string .
    QA_df : pandas dataframe
        QA dataframe object filtered using the asinId recieved and
        converted into pandas dataframe.
    RV_df : pandas dataframe
        Review dataframe object filtered using the asinId recieved
        and converted into pandas dataframe.
    """

    def __init__(self, queryJson, QA_df, RV_df):
        """Initialize the input variables.

        Parameters
        -----------
        queryJson : json string
            User query passed as a json string.
        QA_df : json object of dataframe
            asinId filtered json object of QA dataframe.
        RV_df : json object of dataframe
            asinId filtered json object of review dataframe.
        """
        self.queryJson = queryJson
        self.QA_df = pd.DataFrame(list(QA_df))
        self.RV_df = pd.DataFrame(list(RV_df))

    def engine(self):
        """Main engine that processes the input and produces results.

        Parameters
        ----------
        None

        Returns
        -------
        sendBackJson : dictionary
            A dictionary of values that are processed for the user query.
            Keys of the dictionary are:
            - 'answer'
            - 'answer_sentiments'
            - 'qaRelScore'
            - 'reviews'
            - 'review_sentiments'
            - 'rvRelScore'
        """
        # Step 1: Extract query from json
        query = self.queryJson

        # Step 2 : Process the query
        processed_query, WH_flag = QueryHandler.query_processing(query)

        # Step 2.1 : Handle invalid query
        if len(processed_query) == 0:
            answerJson = {'answer': None,
                          'answer_sentiments': None, 'qaRelScore': None}
            reviewJson = {'reviews': None,
                          'review_sentiments': None, 'rvRelScore': None}
            sendBackJson = self.merged(answerJson, reviewJson)
            return sendBackJson

        # Step 3 : Extract relevant answers and
        #          relevant reviews.
        relAnswer, relReviews = self.find_relevant_stuff(
            processed_query, WH_flag)

        # Step 4 : Create return json
        sendBackJson = self.merged(relAnswer, relReviews)

        return sendBackJson

    def find_relevant_stuff(self, processed_query, WH_flag):
        """Finds the most relevant answers and reviews along with their
           sentiments and relevance scores.

        Parameters
        ----------
        processed_query : list of tokenized string
            user query after processing
        WH_flag : binary
            0 if the query is a 'yes/no' question
            1 if the query is an 'open-ended' question

        Returns
        -------
        relAnswer : dictionary
            dictionary of relevant answer+sentiment+relevanceScore
        relReviews : dictionary
            dictionary of relevant reviews+sentiment+relevanceScore
        """
        # Check for asinId in recieved dataframes
        val = self.check_asin_id()

        if val == 0:
            relAnswer, relReviews = self.present_in_both(
                processed_query, WH_flag)
        elif val == 1:
            relAnswer, relReviews = self.present_only_in_rv(processed_query)
        elif val == 2:
            relAnswer, relReviews = self.present_only_in_qa(
                processed_query, WH_flag)
        elif val == 3:
            relAnswer, relReviews = self.not_present_in_both()

        return relAnswer, relReviews

    def check_asin_id(self):
        """Check for asinId on both dataframes

        Parameters
        ----------
        None

        Returns
        -------
        val : Integer
            Integer value ranging from 0-3 depending on the
            presence of asinId on either or both or none of the dataframes.
        """
        # check if asinId is present in QA, 0 if True else 1
        x = 0 if len(self.QA_df) != 0 else 1
        # check if asinId is present in RV, 0 if True else 2
        y = 0 if len(self.RV_df) != 0 else 2

        # return the sum
        Sum = x + y
        # such that:
        # 0 = Present in both
        # 1 = NOT present in QA but Present in RV
        # 2 = Present in QA but NOT present in RV
        # 3 = NOT present in both
        return Sum

    def present_in_both(self, processed_query, WH_flag):
        """If asinId present in both QA and review dataframe, process the query
           and return the result.

        Parameters
        ----------
        processed_query : list of tokenized string
            user query after processing
        WH_flag : binary
            0 if the query is a 'yes/no' question
            1 if the query is an 'open-ended' question

        Returns
        -------
        answerJson : dictionary
            dictionary of relevant answer+sentiment+relevanceScore
        reviewJson : dictionary
            dictionary of relevant reviews+sentiment+relevanceScore
        """
        # Create answer json
        if len(WH_flag) == 0:
            newDF = self.QA_df[self.QA_df['question_type'] == "yes/no"]
        else:
            newDF = self.QA_df[self.QA_df['question_type'] == "open-ended"]

        if len(newDF) == 0:
            answerJson = {'answer': "Oops! No relevant answer found for your question type!",
                          'answer_sentiments': None, 'qaRelScore': None}
        else:
            flag = 'q'
            df = RelevanceCheck.relevance_finder(processed_query, newDF, flag)
            answer = df['answer'].iloc[0]
            ansSentiment = df['answer_sentiments'].iloc[0]
            ansRelScore = df['relevance_score'].iloc[0]

            if ansRelScore == 0:
                answerJson = {'answer': "Sorry! No relevant answer found for your question.",
                              'answer_sentiments': None, 'qaRelScore': None}
            else:
                answerJson = {'answer': answer, 'answer_sentiments': ansSentiment,
                              'qaRelScore': ansRelScore}

        # Create review json
        flag = 'r'
        df = RelevanceCheck.relevance_finder(processed_query, self.RV_df, flag)
        reviews, revSentiments, revRelScore = self.review_generator(df, ansSentiment)
        # reviews = list(df['reviewText'].iloc[0:5])
        # revSentiments = list(df['review_sentiments'].iloc[0:5])
        # revRelScore = list(df['relevance_score'].iloc[0:5])

        if revRelScore[0] == 0:
            msg = ["Sorry! No relevant reviews found!"]
            reviewJson = {'reviews': msg,
                          'review_sentiments': None, 'rvRelScore': None}
        else:
            reviewJson = {'reviews': reviews,
                          'review_sentiments': revSentiments, 'rvRelScore': revRelScore}

        return answerJson, reviewJson

    def present_only_in_rv(self, processed_query):
        """If asinId is present only in review dataframe, process the query
            and return the result.

        Parameters
        ----------
        processed_query : list of tokenized string
            user query after processing

        Returns
        -------
        answerJson : dictionary
            dictionary of relevant answer+sentiment+relevanceScore
        reviewJson : dictionary
            dictionary of relevant reviews+sentiment+relevanceScore
        """
        # default
        answerJson = {'answer': None,
                      'answer_sentiments': None, 'qaRelScore': None}

        flag = 'r'
        ansSentiment = 'None'
        df = RelevanceCheck.relevance_finder(processed_query, self.RV_df, flag)
        reviews, revSentiments, revRelScore = self.review_generator(df, ansSentiment)
        # reviews = list(df['reviewText'].iloc[0:5])
        # revSentiments = list(df['review_sentiments'].iloc[0:5])
        # revRelScore = list(df['relevance_score'].iloc[0:5])

        if revRelScore[0] == 0:
            msg = ["Sorry! No relevant reviews found!"]
            reviewJson = {'reviews': msg,
                          'review_sentiments': None, 'rvRelScore': None}
        else:
            reviewJson = {'reviews': reviews,
                          'review_sentiments': revSentiments, 'rvRelScore': revRelScore}

        return answerJson, reviewJson

    def present_only_in_qa(self, processed_query, WH_flag):
        """If asinId is present only in QA dataframe, process the query and
            return the result.

        Parameters
        ----------
        processed_query : list of tokenized string
            user query after processing
        WH_flag : binary
            0 if the query is a 'yes/no' question
            1 if the query is an 'open-ended' question

        Returns
        -------
        answerJson : dictionary
            dictionary of relevant answer+sentiment+relevanceScore
        reviewJson : dictionary
            dictionary of relevant reviews+sentiment+relevanceScore
        """
        if len(WH_flag) == 0:
            newDF = self.QA_df[self.QA_df['question_type'] == "yes/no"]
        else:
            newDF = self.QA_df[self.QA_df['question_type'] == "open-ended"]

        if len(newDF) == 0:
            answerJson = {'answer': "Oops! No relevant answer found for your question type!",
                          'answer_sentiments': None, 'qaRelScore': None}
        else:
            flag = 'q'
            df = RelevanceCheck.relevance_finder(processed_query, newDF, flag)
            answer = df['answer'].iloc[0]
            ansSentiment = df['answer_sentiments'].iloc[0]
            ansRelScore = df['relevance_score'].iloc[0]

            if ansRelScore == 0:
                answerJson = {'answer': "Sorry! No relevant answer found for your question.",
                              'answer_sentiments': None, 'qaRelScore': None}
            else:
                answerJson = {'answer': answer, 'answer_sentiments': ansSentiment,
                              'qaRelScore': ansRelScore}

        # default
        reviewJson = {'reviews': None,
                      'review_sentiments': None, 'rvRelScore': None}

        return answerJson, reviewJson

    def not_present_in_both(self):
        """If asinId is not present in both the dataframes, return default reply.

        Parameters
        ----------
        None

        Returns
        -------
        answerJson : dictionary
            dictionary of relevant answer+sentiment+relevanceScore
        reviewJson : dictionary
            dictionary of relevant reviews+sentiment+relevanceScore
        """
        answerJson = {'answer': None,
                      'answer_sentiments': None, 'qaRelScore': None}
        reviewJson = {'reviews': None,
                      'review_sentiments': None, 'rvRelScore': None}

        return answerJson, reviewJson

    def review_generator(self, dataframe, answerSentiment):
        """Generates top relevant and complimentary reviews

        Parameters
        ----------
        dataframe : pandas dataframe
            review dataframe sorted by their relevancy scores
        answerSentiment : string
            sentiment of the answer to user's query

        Returns
        -------
        reviews : list
            list of user reviews
        revSentiments : list
            list of the sentiment scores of the reviews
        revRelScore : list
            list of the relevance scores of the reviews
        """
        review1 = dataframe['reviewText'].iloc[0]
        review1Sentiments = dataframe['review_sentiments'].iloc[0]
        review1RelScore = dataframe['relevance_score'].iloc[0]

        if answerSentiment == 'positive':
            ndf = dataframe[dataframe['review_sentiments'] == 'negative']

            if len(ndf) == 0:  # No negative reviews
                review2 = dataframe['reviewText'].iloc[1]
                review3 = dataframe['reviewText'].iloc[2]
                review2Sentiments = dataframe['review_sentiments'].iloc[1]
                review3Sentiments = dataframe['review_sentiments'].iloc[2]
                review2RelScore = dataframe['relevance_score'].iloc[1]
                review3RelScore = dataframe['relevance_score'].iloc[2]
            elif len(ndf) == 1:  # Only 1 negative review
                review2 = dataframe['reviewText'].iloc[1]
                review3 = ndf['reviewText'].iloc[0]
                review2Sentiments = dataframe['review_sentiments'].iloc[1]
                review3Sentiments = ndf['review_sentiments'].iloc[0]
                review2RelScore = dataframe['relevance_score'].iloc[1]
                review3RelScore = ndf['relevance_score'].iloc[0]
            else:  # More than 1 negative review
                review2 = ndf['reviewText'].iloc[0]
                review3 = ndf['reviewText'].iloc[1]
                review2Sentiments = ndf['review_sentiments'].iloc[0]
                review3Sentiments = ndf['review_sentiments'].iloc[1]
                review2RelScore = ndf['relevance_score'].iloc[0]
                review3RelScore = ndf['relevance_score'].iloc[1]

        elif answerSentiment == 'negative':
            ndf = dataframe[dataframe['review_sentiments'] == 'positive']

            if len(ndf) == 0:  # No positive reviews
                review2 = dataframe['reviewText'].iloc[1]
                review3 = dataframe['reviewText'].iloc[2]
                review2Sentiments = dataframe['review_sentiments'].iloc[1]
                review3Sentiments = dataframe['review_sentiments'].iloc[2]
                review2RelScore = dataframe['relevance_score'].iloc[1]
                review3RelScore = dataframe['relevance_score'].iloc[2]
            elif len(ndf) == 1:  # Only 1 positive review
                review2 = dataframe['reviewText'].iloc[1]
                review3 = ndf['reviewText'].iloc[0]
                review2Sentiments = dataframe['review_sentiments'].iloc[1]
                review3Sentiments = ndf['review_sentiments'].iloc[0]
                review2RelScore = dataframe['relevance_score'].iloc[1]
                review3RelScore = ndf['relevance_score'].iloc[0]
            else:  # More than 1 positive review
                review2 = ndf['reviewText'].iloc[0]
                review3 = ndf['reviewText'].iloc[1]
                review2Sentiments = ndf['review_sentiments'].iloc[0]
                review3Sentiments = ndf['review_sentiments'].iloc[1]
                review2RelScore = ndf['relevance_score'].iloc[0]
                review3RelScore = ndf['relevance_score'].iloc[1]

        elif answerSentiment == 'None':
            review2 = dataframe['reviewText'].iloc[1]
            review3 = dataframe['reviewText'].iloc[2]
            review2Sentiments = dataframe['review_sentiments'].iloc[1]
            review3Sentiments = dataframe['review_sentiments'].iloc[2]
            review2RelScore = dataframe['relevance_score'].iloc[1]
            review3RelScore = dataframe['relevance_score'].iloc[2]

        # List everything
        reviews = [review1, review2, review3]
        revSentiments = [review1Sentiments, review2Sentiments, review3Sentiments]
        revRelScore = [review1RelScore, review2RelScore, review3RelScore]

        return reviews, revSentiments, revRelScore

    def merged(self, dic1, dic2):
        """Merge two dictionaries together

        Parameters
        ----------
        dic1 : dictionary
            answerJson dictionary
        dic2 : dictionary
            reviewJson dictionary

        Returns
        -------
        dic : dictionary
            combined dictionary of dic1 and dic2
        """
        dic = dic1.copy()
        dic.update(dic2)
        return dic
