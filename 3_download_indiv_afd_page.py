from __future__ import print_function
from bs4 import BeautifulSoup
import boto3
import csv
import datetime
import io
import pandas as pd
import sys
from src import scraping
from src import data


wikipedia_prefix = 'https://en.wikipedia.org/wiki/'
wikipedia_domain = 'https://en.wikipedia.org/'
data_directory = ''

# intialize connection to S3 resources
s3 = boto3.resource('s3')
s3_client = boto3.client('s3', 'us-east-1')

output = 's3'
s3_buckets = {"scraped": "afd-scraped"}


def lambda_handler(event, context):
    print("Event Records")
    print(event['Records'])
    print("******")

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        print("Event: {}".format(key))


        obj = s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()))
        print(df)

        page_url = df['url'].values[0]
        page_afd = df['afd_url'].values[0]
        page_id = df['id'].values[0]
        daily_log_page = df['page'].values[0]
        scrape_date = df['scrape_date'].values[0]

        # download the actual html of the page nominated for deletion
        page_url_html = scraping.download_html(page_url, wikipedia_domain)

        # store html to
        scraping.store_html(page_url_html, 'individual_afd_page_html', data_directory, 's3',fileName=page_id)

        # download the actual html of the page nominated for deletion
        discussion_html = scraping.download_html(page_afd, wikipedia_domain)

        # store html to
        scraping.store_html(discussion_html, 'individual_afd_discussion_page', data_directory, 's3', fileName=page_id)
