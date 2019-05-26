import boto3
from bs4 import BeautifulSoup
import datetime
import numpy as np
import pandas as pd
import re
import requests
import time
from src import utils

s3_buckets = {"scraped":"afd-scraped"}
outputDirectories = {"Wikipedia:Articles_for_deletion": "Articles_for_deletion/",
                    "daily_afd_log": "daily_afd_log/",
                    "individual_afd_page":"individual_afd_page/",
                    "individual_wiki_page":"individual_wiki_page/",
                    "voting": "voting/"}

# intialize connection to S3 resources
s3 = boto3.resource('s3')
s3_client = boto3.client('s3', 'us-east-1')

output = 's3'


timestamp = datetime.datetime.now()
date = str(timestamp).split(" ")[0]

def create_s3_directories():
    # Call S3 to list current buckets
    response = s3_client.list_buckets()
    # Get a list of all bucket names from the response
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    print("Buckets: {}".format(buckets))

    for dir in s3_buckets.values():
        if dir not in buckets:
            dir = dir.replace("/","").replace("_","-").lower()
            print(dir)
            s3_client.create_bucket(Bucket=dir )

    # Call S3 to list current buckets
    response = s3_client.list_buckets()
    # Get a list of all bucket names from the response
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    print("Buckets: {}".format(buckets))


@utils.timeit
def download_html(urlString,prefix,**kwargs):
    '''
    Connects to the webpage prefix+urlString and downloads html
    :param urlString: URL string after prefix
    :param prefix: Prefix before URL string (ex 'https://en.wikipedia.org/')
    :param kwargs:
    :return: HTML content from prefix+urlString
    '''
    print(urlString)
    try:
        start = time.time()
        html = requests.get(prefix + urlString)
        html = html.text
        print(html[0:10])
    except:
        print("Could not connect to {}".format(str(prefix) + str(urlString)))
        html = np.NaN
    end = time.time()
    print("Download HTML Time: {}".format(end - start))
    return html

def extract_ahref(parsedHtml):
    '''
    Extract all <a href> tags from a BeautifulSoup object
    :param parsedHtml: BeautifulSoup object
    :return: a list of href attributes in <a> tags
    '''
    links = [x.get('href') for x in parsedHtml.find_all('a')]
    links = [x for x in links if x is not None]
    return links

def extract_log_id_and_url(parsed):
    start = time.time()
    id_url = []
    print("Running extract_log_id_and_url")
    for h in parsed.find_all('h3'):
        for s in h.find_all('span', attrs={"class": "mw-headline"}):
            for a in s.find_all('a'):
                print(a)
                id_url.append(s.get('id')+"___"+a.get('href'))
    end = time.time()
    print("Extract URLs time: {}".format(end - start))
    return id_url

@utils.timeit
def find_afd_stats_by_id(parsed,**kwargs):
    id = kwargs.get('id')
    for dd in parsed.find_all('dd'):
        if id in str(dd):
            a = dd.find("a", href=re.compile("wmflabs.org/jackbot"))
            if a is not None:
                return [id,a.get('href')]
            else:
                return [id,np.NaN]
            
@utils.timeit
def find_indiv_afd_by_id(parsed,**kwargs):
    '''
    On a daily AFD page, search for the unique identifier of a page that has been nominated for deletion.
    Return the URL of the page nominated for deletion
    :param parsed:
    :param kwargs:
    :return:
    '''
    id = kwargs.get('id')
    for dd in parsed.find_all('dd'):
        if id in str(dd):
            a = dd.find("a", title=re.compile("Wikipedia:Articles for deletion/"),href=True)
            if a is not None:
                return [id,a.get('href')]
            else:
                return [id,np.NaN]

def generate_df_of_daily_logs(ahrefList):
    '''
    Search list of href attributes to identify links that contain "_deletion/Log",
    a substring that exists in article for deletion log pages
    :param ahrefList: A list of href attributes
    :return:  A list of links to article for deletion pages
    '''
    logs = [x for x in ahrefList if "_deletion/Log" in x]
    logs = list(set(logs))
    logDF = pd.DataFrame({"log_url":logs})
    
    # urls we want always end with date as in 'February_1'
    # drop rows that do not end in an int
    
    logDF['last_char'] = logDF['log_url'].apply(lambda x: x[-1])
    
    def convertToInt(x):
        try:
            int(x)
            return True
        except:
            return False
    logDF['last_char_as_int'] = logDF['last_char'].apply(lambda x: convertToInt(x))
    
    return logDF[logDF['last_char_as_int']].drop("last_char_as_int",axis=1).drop("last_char",axis=1)

@utils.timeit
def open_page(bucket,key,*args,**kwargs):
    obj = s3.Object(bucket, key)
    obj_text = obj.get()['Body'].read().decode('utf-8')

    print("First 20 char: {}".format(obj_text[0:20]))

    parsed = BeautifulSoup(obj_text,'html.parser')

    print("Parsed beautiful soup")

    results = [key]

    print("Args: {}".format(args))
    for arg in args:
        print("arg in open_page: {}".format(arg))
        results.append(arg(parsed,**kwargs))

    print("Results: {}".format(results))
    return results


def store_string(string, typeOfRequest, fileName=''):
    if fileName != '':
        s3_client.put_object(Body=bytes(string, 'utf-8'),
                         Bucket=s3_buckets['scraped'],
                         Key=outputDirectories[typeOfRequest] + date +"/{}".format(fileName) + ".txt",
                         )

    else:
        s3_client.put_object(Body=bytes(string, 'utf-8'),
                             Bucket=s3_buckets['scraped'],
                             Key=outputDirectories[typeOfRequest] + date + ".txt",
                             )




def store_html(html_text,typeOfRequest,dataDirectory,output,fileName=''):
    start = time.time()
    timestamp = datetime.datetime.now()
    date = str(timestamp).split(" ")[0]
    print(output)
    
    if typeOfRequest == "Wikipedia:Articles_for_deletion":
        
        if output=="local":
            log_file = open(dataDirectory + "scraped/"+outputDirectories[typeOfRequest] + date + ".txt", "w")
            log_file.write(html_text)
            log_file.close()
        
        if output == 's3':
            s3_client.put_object( Body=bytes(html_text,'utf-8'),
                                 Bucket = s3_buckets['scraped'],
                                 Key = outputDirectories[typeOfRequest]+date+".txt",
                                 )
    else:
        if output=="local":
            if os.path.exists(dataDirectory + "scraped/" + outputDirectories[typeOfRequest] + date)==False:
                os.mkdir(dataDirectory + "scraped/" + outputDirectories[typeOfRequest] + date)
        
            log_file = open(dataDirectory + "scraped/" + outputDirectories[typeOfRequest] + date +"/" + fileName+ ".txt", "w")
            log_file.write(str(html_text))
            log_file.close()
        
        if output=='s3':
            s3_client.put_object(Body=bytes(html_text, 'utf-8'),
                                 Bucket=s3_buckets['scraped'],
                                 Key=outputDirectories[typeOfRequest] + date +"/" + fileName + ".txt",
                                 )

    end = time.time()
    print("storing html extract_statstime: {}".format(end - start))