import boto3
from bs4 import BeautifulSoup
import datetime
import numpy as np
import os
import pandas as pd
import re
import requests
import time
from src import utils
from src import data

s3_buckets = {"scraped":"afd-scraped"}
outputDirectories = {"Wikipedia:Articles_for_deletion": "Articles_for_deletion/",
                    "daily_afd_log": "daily_afd_log/",
                    "daily_afd_analysis": "daily_afd_analysis/",
                    "individual_afd_analysis":"individual_afd_analysis/",
                    "individual_afd_page":"individual_afd_page/",
                     "individual_afd_page_html": "individual_afd_page_html/",
                     "individual_afd_discussion_page": "individual_afd_discussion_page/",
                    "individual_wiki_page":"individual_wiki_page/",
                    "voting": "voting/"}

# intialize connection to S3 resources
s3 = boto3.resource('s3')
s3_client = boto3.client('s3', 'us-east-1')

output = 's3'


timestamp = datetime.datetime.now()
date = str(timestamp).split(" ")[0]

def create_s3_directories():
    '''
        Create required S3 buckets if they do not already exist
        '''
    response = s3_client.list_buckets()
    
    current_buckets = [bucket['Name'] for bucket in response['Buckets']]
    print("Current Buckets: {}".format(current_buckets))
    
    for required_bucket in s3_buckets.values():
        if required_bucket not in current_buckets:
            s3_client.create_bucket(Bucket=required_bucket )
            print("Created {} bucket".format(required_bucket))


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
    '''
    Extract an identifier and URL for individual pages nominated for deletion
    The page ID is stored in the id attribute of span class="mw-headline"
    The page URL is stored in the a href tag nested under span class="mw-headline"
    :param parsed: A string in the format [id]___[url]
    :return:
    '''
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
    '''
     On a daily AFD page, search for the unique identifier of a page that has been nominated for deletion.
     Return the URL of the page where wikipedia community members vote on the afd decision
    :param parsed:
    :param kwargs:
    :return:
    '''
    id = kwargs.get('id')
    for dd in parsed.find_all('dd'):
        if id in str(dd):
            a = dd.find("a", href=re.compile("wmflabs.org/jackbot"))
            if a is not None:
                return [id,a.get('href')]
            else:
                return [id,np.NaN]


def find_comment_author(parsedComment):
    '''
        Author user names can be found in the 'title' of <a> tags .
        The user name is usually prefaced by "User:" or "Usertalk:", so we split by ":"
        :param parsedComment:
        :return: string with the comment's author, if found
        '''
    links = parsedComment.find_all("a")
    for a in links:
        title = a.get('title')
        if title is not None:
            if ("User" in title) and (":" in title):
                return title.split(":")[1]
    return np.NaN

            
@utils.timeit
def find_indiv_afd_by_id(parsed,**kwargs):
    '''
    On a daily AFD page, search for the unique identifier of a page that has been nominated for deletion.
    Return the URL of the nominated page's article for deletion page
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

def identify_archived_debate(parsed):
    parsed_text = str(parsed)
    if "The following discussion is an archived debate" in parsed_text:
        return True
    else:
        return False



def get_first_afd_comment(parsed,**kwargs):
    parsed_text = str(parsed)
    
    found_comments = []
    commentAuthor = np.NaN
    
    results = [np.NaN,np.NaN]

    
    if "TWL</a></span>)</dd></dl>" in parsed_text:
        text_after_header = parsed_text.split("TWL</a></span>)</dd></dl>")[1]
        parsed_after_header = BeautifulSoup(text_after_header, 'html.parser')
        try:
            found_comments.append(parsed_after_header.find('p'))
            try:
                commentAuthor = find_comment_author(found_comments[-1])

                while pd.isnull(commentAuthor):
                    if found_comments[-1].find_next("p") is not None:
                        found_comments.append(found_comments[-1].find_next("p"))
                        commentAuthor = find_comment_author(found_comments[-1])
                    else:
                        commentAuthor = "NA"
            except:
                results = [found_comments,np.NaN]
        except:
            results = [np.NaN,np.NaN]

    if len(found_comments) >= 1:
        found_comments = [str(x) for x in found_comments]
        final_comments = ' '.join(found_comments)
        results[0] = final_comments
    
    if pd.isnull(commentAuthor)==False and commentAuthor != "NA":
        results[1] = commentAuthor
    return results



def get_later_afd_comments(parsed,**kwargs):
    parsed_text = str(parsed)
        
    if "TWL</a></span>)</dd></dl>" in parsed_text:
        text_after_header = parsed_text.split("TWL</a></span>)</dd></dl>")[1]
        parsed_after_header = BeautifulSoup(text_after_header, 'html.parser')
    else:
        return [np.NaN,np.NaN]
    
    found_comments = []
    found_authors = []
    
    comments = parsed_after_header.find_all('li')
    for li in comments:
        if "AfD debates" not in str(li):
            found_comments.append(li)
            found_authors.append(find_comment_author(found_comments[-1]))
        else:
            break
    return [found_comments, found_authors]

def get_references(parsed,**kwargs):
    reference_urls = []
    references = parsed.find('ol', attrs={"class": "references"})
    if references is not None:
        for li in references.find_all('li'):
            for a in li.find_all('a'):
                link = a.get('href')
                if link is not None:
                    if 'http' in link:
                        reference_urls.append(link)
    return reference_urls

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


def store_string(string, typeOfRequest, fileName='',optional_date=''):
    '''

    :param string: A string to write to s3
    :param typeOfRequest:
    :param fileName:
    :return:
    '''
    if optional_date != '':
        date = optional_date
    else:
        timestamp = datetime.datetime.now()
        date = str(timestamp).split(" ")[0]
    
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




def store_html(html_text,typeOfRequest,fileName=''):
    '''

    :param html_text:
    :param typeOfRequest:
    :param fileName:
    :return:
    '''
    start = time.time()
    timestamp = datetime.datetime.now()
    date = str(timestamp).split(" ")[0]
    
    if typeOfRequest == "Wikipedia:Articles_for_deletion":

        s3_client.put_object( Body=bytes(html_text,'utf-8'),
                                 Bucket = s3_buckets['scraped'],
                                 Key = outputDirectories[typeOfRequest]+date+".txt",
                                 )
    else:
        s3_client.put_object(Body=bytes(html_text, 'utf-8'),
                             Bucket=s3_buckets['scraped'],
                             Key=outputDirectories[typeOfRequest] + date +"/" + fileName + ".txt",
                             )

    end = time.time()
