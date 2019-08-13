from __future__ import print_function
from bs4 import BeautifulSoup
import boto3
import csv
import datetime
import numpy as np
import pandas as pd
from src import scraping
from src import data


wikipedia_prefix = 'https://en.wikipedia.org/wiki/'
wikipedia_domain = 'https://en.wikipedia.org/'
data_directory = ''

# intialize connection to S3 resources
s3 = boto3.resource('s3')
s3_client = boto3.client('s3', 'us-east-1')

output = 's3'
s3_buckets = {"scraped":"afd-scraped"}

timestamp = datetime.datetime.now()
date = str(timestamp).split(" ")[0]


def open_summary_page(df, pageColName, idColName):
    '''
    Open daily AFD pages. Return URLs of pages nominated for deletion
    :param df: indiv_afd_page
    :param pageColName: A column storing daily AFD log pages (i.e. 2019_February_22.txt)
    :param idColName: A column storing the id of a page nominated for deletion (i.e. Nick_Brockmeyer)
    :return: A data frame with one row per page nominated for deletion
    '''
    all_results = pd.DataFrame()

    # iterate through each daily AFD log page (i.e. 2019_February_22.txt)
    for daily_page in df[pageColName].unique():

        #s3://afd-scraped/daily_afd_log/2019-04-13/2019_April_10.txt
        print("File to open: {}".format(daily_page))
        obj = s3.Object('afd-scraped', '{}'.format(daily_page))
        obj_text = obj.get()['Body'].read().decode('utf-8')
        parsed = BeautifulSoup(obj_text, 'html.parser')

        filesThisPage = df[df[pageColName] == daily_page]

        # obtain the article for deletion discussion page for this id
        filesThisPage['indiv_afd_by_id'] = filesThisPage[idColName].apply(lambda x:
                                                                          scraping.find_indiv_afd_by_id(parsed, id=x))
        # obtain the url of the page for voting on afd status for this id
        filesThisPage['afd_stats_by_id'] = filesThisPage[idColName].apply(lambda x:
                                                                          scraping.find_afd_stats_by_id(parsed, id=x))

        if all_results.shape[0] == 0:
            all_results = filesThisPage
        else:
            all_results = all_results.append(filesThisPage)

    return all_results


def lambda_handler(event, context):
    
    print("Event Records")
    print(event['Records'])
    print("******")
    
    for record in event['Records']:

        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        print("Daily Log: {}".format(key))

        # create a data frame to store individual
        daily_afd = pd.DataFrame({"page": key,
                                 "scrape_date": date},index=[0])

        # extract the ID and URL for each page nominated for deletion on "key"
        temp = daily_afd['page'].apply(lambda x: scraping.open_page(bucket, x,scraping.extract_log_id_and_url))

        # create a data frame with the ID and URL of all pages nominated for deletion on "key"
        daily_afd_append = pd.DataFrame.from_items(zip(temp.index, temp.values)).T
        daily_afd_append.columns = ['page','id_url']
        daily_afd = daily_afd.merge(daily_afd_append,on="page")

        # create a data frame with one row per page nominated for deletion on "key"
        indiv_afd_page = data.explode_list_column(daily_afd,'id_url')
        indiv_afd_page = data.split_key_col(indiv_afd_page,'id_url_exploded',['id','url'])

        # find the afd discussion and afd voting pages for each article nominated for deletion
        original = indiv_afd_page.shape[0]
        indiv_afd_page = open_summary_page(indiv_afd_page,
                                           'page',
                                           'id')
        assert indiv_afd_page.shape[0] == original

        # extract the afd discussion and voting urls
        indiv_afd_page['afd_url'] = indiv_afd_page['indiv_afd_by_id'].apply(lambda x: x[1] if x is not None else np.NaN)
        indiv_afd_page['voting_url'] = indiv_afd_page['afd_stats_by_id'].apply(
            lambda x: str(x[1]) if x is not None else np.NaN)

        # save the data collected for each afd page separately to afd-scraped/individual_afd_page/[run date]/row[id'].txt
        for index, row in indiv_afd_page.iterrows():
            rowDF = row.to_frame().T
            rowString = rowDF.to_csv( quoting=csv.QUOTE_NONNUMERIC,index=False)
            scraping.store_string(rowString, "individual_afd_page", fileName=row['id'])

