from __future__ import print_function
from bs4 import BeautifulSoup
import boto3
from src import scraping


wikipedia_prefix = 'https://en.wikipedia.org/wiki/'
wikipedia_domain = 'https://en.wikipedia.org/'
data_directory = ''

# intialize connection to S3 resources
s3 = boto3.resource('s3')
s3_client = boto3.client('s3', 'us-east-1')

output = 's3'
s3_buckets = {"scraped":"afd-scraped"}


def lambda_handler(event, context):
    scraping.create_s3_directories()
    print("created directories")

    # download https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion
    afd_homepage = scraping.download_html('Wikipedia:Articles_for_deletion', wikipedia_prefix)

    # store afd page to  to s3/afd-scraped/Articles_for_deletion/[date].txt
    scraping.store_html(afd_homepage, 'Wikipedia:Articles_for_deletion', data_directory, 's3')

    # parse afd page
    afd_homepage_parsed = BeautifulSoup(afd_homepage, 'html.parser')
    print("Parsed HTML")

    # extract all href attributes on the Articles for Deletion page
    afd_homepage_links = scraping.extract_ahref(afd_homepage_parsed)
    print("Obtained URLs: {}".format(afd_homepage_links[0:3]))

    # download daily afd logs (i.e. pages in the format https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion/Log/2019_May_22)
    daily_afd = scraping.generate_df_of_daily_logs(afd_homepage_links)
    daily_afd['response'] = daily_afd['log_url'].apply(lambda x: scraping.download_html(x, wikipedia_domain))

    # store the daily afd logs at afd-scraped/daily_afd_log/[scraping-date]/[AFD log date].txt
    daily_afd[['response', 'log_url']].apply(
        lambda x: scraping.store_html(x[0], 'daily_afd_log', data_directory, output='s3', fileName=x[1].split("/")[-1]),
        axis=1)
