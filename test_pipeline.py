import boto3
from bs4 import BeautifulSoup
import datetime
from freezegun import freeze_time
import math
from moto import mock_s3
import numpy as np
import pandas as pd
import pytest
from src import data
from src import scraping

wikipedia_domain = 'https://en.wikipedia.org/'

# read in sample master AFD homepage
afd_file = open('./tests/files/Wikipedia_Articles_for_deletion.html',
                'r', encoding='utf-8')
afd_html = afd_file.read()
afd_homepage_parsed = BeautifulSoup(afd_html, 'html.parser')


# read in sample daily afd log
daily_afd_log___2019_08_12 = open('./tests/files/daily_afd_log/2019-08-25/2019_August_12.html',
                'r', encoding='utf-8')
daily_afd_log___2019_08_12_html = daily_afd_log___2019_08_12.read()
daily_afd_log___2019_08_12_parsed = BeautifulSoup(daily_afd_log___2019_08_12_html, 'html.parser')
log_id_urls = scraping.extract_log_id_and_url(daily_afd_log___2019_08_12_parsed)

# read in sample individual wiki page
individual_afd_page_html___jeff_sebastian = open('./tests/files/individual_afd_page_html/2019-08-25/Jeff_Sebastian.txt',
                'r', encoding='utf-8')
individual_afd_page_html___jeff_sebastian = individual_afd_page_html___jeff_sebastian.read()
individual_afd_page_html___jeff_sebastian_parsed = BeautifulSoup(individual_afd_page_html___jeff_sebastian, 'html.parser')


def test_extract_ahref():
    links = scraping.extract_ahref(afd_homepage_parsed)
    assert links[0][0:43] == 'https://en.wikipedia.org/w/load.php?lang=en'
    assert len(links)==832

def test_extract_log_id_and_url():
    log_id_urls = scraping.extract_log_id_and_url(daily_afd_log___2019_08_12_parsed)
    assert log_id_urls[0] == 'Jeff_Sebastian___/w/index.php?title=Jeff_Sebastian&action=edit&redlink=1'
    assert log_id_urls[1] == 'Robert_Farber_(artist)___/wiki/Robert_Farber_(artist)'

def test_find_indiv_afd_by_id():
    indiv_afd_id = scraping.find_indiv_afd_by_id(daily_afd_log___2019_08_12_parsed, id='Jeff_Sebastian')
    assert indiv_afd_id == ['Jeff_Sebastian', '/wiki/Wikipedia:Articles_for_deletion/Jeff_Sebastian']

def test_find_afd_stats_by_id():
    afd_stats = scraping.find_afd_stats_by_id(daily_afd_log___2019_08_12_parsed, id='Jeff_Sebastian')
    assert afd_stats == ['Jeff_Sebastian',
                         'https://tools.wmflabs.org/jackbot/snottywong/cgi-bin/votecounter.cgi?page=Wikipedia:Articles_for_deletion/Jeff_Sebastian']

def test_generate_df_of_daily_logs():
    links = scraping.extract_ahref(afd_homepage_parsed)
    df_daily_logs = scraping.generate_df_of_daily_logs(links)
    assert df_daily_logs['log_url'].values[0] == 'https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion/Log/2019_August_12'


def test_is_person_by_card():
    assert math.isnan(data.is_person_by_card(individual_afd_page_html___jeff_sebastian_parsed))

def test_is_person_by_category():
    assert math.isnan(data.is_person_by_category(individual_afd_page_html___jeff_sebastian_parsed))

@mock_s3
def test_1_download_daily_afd_log():
    '''
    Test storing daily afd logs to S3
    '''
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3', 'us-east-1')
    s3_client.create_bucket(Bucket='afd-scraped')

    afd_homepage_links = scraping.extract_ahref(afd_homepage_parsed)
    daily_afd = scraping.generate_df_of_daily_logs(afd_homepage_links)

    # read in a saved HTML page
    daily_afd['response'] = daily_afd_log___2019_08_12_html

    #store_html uses the current date in naming a file
    # use froze date associated with saved files in test folder
    freezer = freeze_time("2019-08-25")
    freezer.start()

    daily_afd[['response', 'log_url']].apply(lambda x:
                                             scraping.store_html(s3_client,
                                                                x[0],
                                                                 'daily_afd_log',
                                                                 fileName=x[1].replace(
                                                                     "https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion/Log/", "")),
                                             axis=1)

    todays_date = str(datetime.datetime.now()).split(" ")[0]
    freezer.stop()

    obj = s3.Object('afd-scraped', 'daily_afd_log/{}/2019_August_12.txt'.format(todays_date))
    obj_text = obj.get()['Body'].read().decode('utf-8')

    assert 'Octaviano Tenorio' in obj_text
    assert 'Mohana Krishna' in obj_text
