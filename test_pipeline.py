from bs4 import BeautifulSoup
import pandas as pd
import pytest
from src import scraping

afd_file = open('./tests/files/Wikipedia_Articles_for_deletion.html',
                'r', encoding='utf-8')
afd_html = afd_file.read()
afd_homepage_parsed = BeautifulSoup(afd_html, 'html.parser')

def test_extract_ahref():
    links = scraping.extract_ahref(afd_homepage_parsed)
    assert links[0][0:43] == 'https://en.wikipedia.org/w/load.php?lang=en'
    assert len(links)==832

def test_generate_df_of_daily_logs():
    links = scraping.extract_ahref(afd_homepage_parsed)
    df_daily_logs = scraping.generate_df_of_daily_logs(links)
    assert df_daily_logs['log_url'].values[0] == 'https://en.wikipedia.org/wiki/Wikipedia:Articles_for_deletion/Log/2019_August_12'

