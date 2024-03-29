import io
import logging
import numpy as np
import os
import pandas as pd
import boto3
import urllib


def append_dataframes(master_df,new_df):
    if master_df.shape[0] == 0:
        master_df = new_df
    else:
        master_df = master_df.append(new_df)
    return master_df

def decode_s3_key(s3_key_name):
    '''
    Replace HTML escape characters with their single character equivalent
    '''
    return urllib.parse.unquote_plus(s3_key_name)

def flatten_list(l):
    return [item for sublist in l for item in sublist]

def generate_df_of_files_in_directory(data_directory,data_type,date):
    afd_pages = os.listdir("{}scraped/{}/{}/".format(data_directory,data_type, date))
    afd_pages = pd.DataFrame({"page": afd_pages, "scrape_date": [date] * len(afd_pages)})
    return afd_pages

def get_keys_in_bucket(s3_client,bucket,prefix):
    keys_response = s3_client.list_objects_v2(Bucket=bucket,Prefix=prefix)
    contents = keys_response['Contents']
    keys = [x['Key'] for x in contents]
    return keys

def return_files_in_bucket(bucket):
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3', 'us-east-1')
    afd_pages = s3_client.list_objects_v2(Bucket=bucket)
    return afd_pages
    
def return_keys_with_folder(bucket_contents,folderNamesList):
    keys = []
    num_folders = len(folderNamesList)
    for c in bucket_contents:
        key = c.get('Key')
        for i in range(0,num_folders):
            if i < (num_folders-1):
                if folderNamesList[i] in key:
                    continue
                else:
                    break
            if i == (num_folders-1):
                if folderNamesList[i] in key:
                    keys.append(key)
                else:
                    break

    return keys
            

def generate_df_of_files_in_bucket(bucket,folderNamesList,date):
    bucket_contents = return_files_in_bucket(bucket=bucket).get('Contents')
    bucket_keys = return_keys_with_folder(bucket_contents,folderNamesList)
    afd_pages = pd.DataFrame({"page": bucket_keys, "scrape_date": [date] * len(bucket_keys)})
    return afd_pages

    

def explode_list_column(df,column_to_explode):
    res = (df
           .set_index([x for x in df.columns if x != column_to_explode])[column_to_explode]
           .apply(pd.Series)
           .stack()
           .reset_index())
    res = res.rename(columns={
              res.columns[-2]:'exploded_{}_index'.format(column_to_explode),
              res.columns[-1]: '{}_exploded'.format(column_to_explode)})
    return res

def split_key_col(df,key_column,key_name_list):
    for i in range(len(key_name_list)):
        df[key_name_list[i]] = df[key_column].apply(lambda x: x.split("___")[i])
    return df

def is_person_by_card(wikiHtml,**kwargs):
    is_person = np.NaN
    try:
        for t in wikiHtml.findAll('table',{"class": "infobox biography vcard"}):
            if 'Born' in t.text:
                is_person = True
            else:
                is_person = False
    except:
        print('could not find table')
    return is_person

def is_person_by_category(wikiHtml,**kwargs):
    is_person = np.NaN
    try:
        for t in wikiHtml.findAll('div',{"id": "mw-normal-catlinks"}):
            if 'people' in t.text:
                is_person = True
            else:
                is_person = False
    except:
        print('could not find table')
    return is_person

def count_pronouns(parsedHTML,pronoun_to_search, **kwargs):
    '''
    Counts the number of instances of pronouns in an HTML file
    :param parsedHTML: HTML file parsed by BeautifulSoup
    :param pronoun_to_search: String representing a pronoun to count
    '''
    pronoun_dict = {"she":['she','her'],
                    "he": ['he','his'],
                    "they": ['they','their'],
                    "nonbinary": ['nonbinary']}

    text =  parsedHTML.get_text()
    count = 0

    if len(pronoun_dict.get(pronoun_to_search,[])) > 0:
        for pronoun in pronoun_dict[pronoun_to_search]:
            count = count + text.lower().count(' {} '.format(pronoun))

    else:
        raise ValueError('{} does not exist in dictionary'.format(pronoun_to_search))

    return count

def count_he(parsedHTML,**kwargs):
    text =  parsedHTML.get_text()
    count = 0
    try:
        count = count + text.lower().count(' he ')
        count = count + text.lower().count(' his ')
    except:
        print("could not count")
    return count

def count_they(parsedHTML,**kwargs):
    text =  parsedHTML.get_text()
    count = 0
    try:
        count = count + text.lower().count(' they ')
        count = count + text.lower().count(' their ')
    except:
        print("could not count")
    return count

def count_nonbinary(parsedHTML,**kwargs):
    text =  parsedHTML.get_text()
    count = 0
    try:
        count = count + text.lower().count(' nonbinary ')
    except:
        print("could not count")
    return count

def gather_afd(dateList,data_directory):
    # grab all afd pages
    individual_afd = pd.DataFrame()
    for d in dateList:
        if individual_afd.shape[0] == 0:
            individual_afd = pd.read_csv("{}processed/{}/comment_with_label.csv".format(data_directory, d))
            individual_afd['scrape_date'] = d
        else:
            temp = pd.read_csv("{}processed/{}/comment_with_label.csv".format(data_directory, d))
            temp['scrape_date'] = d
            individual_afd = individual_afd.append(temp)
    individual_afd['scrape_date'] = pd.to_datetime(individual_afd['scrape_date'])
    individual_afd = individual_afd.drop("exploded_id_url_index", axis=1).drop("page_AFDDaily", axis=1)
    individual_afd = individual_afd.drop_duplicates()
    return individual_afd

def find_most_recent_afd_page(individual_afd):
    '''
    if one afd page has multiple scrapes, keep most recent
    :param individual_afd:
    :return:
    '''
    mostRecentScrape = individual_afd.groupby(['afd_url']).agg({"scrape_date": lambda x: max(x)}).reset_index()
    individual_afd = individual_afd.merge(mostRecentScrape, on="afd_url", suffixes=['', '_max'])
    individual_afd['scrape_date_max'] = pd.to_datetime(individual_afd['scrape_date_max'])
    individual_afd = individual_afd[individual_afd['scrape_date'] == individual_afd['scrape_date_max']]
    return individual_afd

def explode_col(column_to_explode,df):
    res = (df
           .set_index([x for x in df.columns if x != column_to_explode])[column_to_explode]
           .apply(pd.Series)
           .stack()
           .reset_index())
    res = res.rename(columns={
              res.columns[-2]:'exploded_{}_index'.format(column_to_explode),
              res.columns[-1]: '{}_exploded'.format(column_to_explode)})
    return res


def extract_runtimes(file, log_type, date_filter=''):
    '''
    log_type: 'INFO','DEBUG'
    date: limit to a specified date, if desired. for all dates, leave blank.
    '''
    logDF = pd.DataFrame()
    for line in file:
        # only review lines that are of the specified line type
        if line[0:len(log_type)] == log_type:
            function = line.split(":")[2].split(" ")[0]
            date = line.split("runtime at ")[1].split(" ")[0]

            # exit if not specified date
            if date_filter != '':
                if date_filter != date:
                    continue

            runtime = line.split(":")[-1].rstrip().lstrip()
            try:
                runtime = int(runtime)
            except:
                runtime = np.NaN

            if logDF.shape[0] == 0:
                logDF = pd.DataFrame({"function": function,
                                      "date": date,
                                      "runtime": runtime}, index=[0])
            else:
                temp = pd.DataFrame({"function": function,
                                     "date": date,
                                     "runtime": runtime}, index=[0])
                logDF = logDF.append(temp)
    return logDF

def read_csv_on_s3(s3_client,bucket,key):
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    return df

def select_gender_identity(is_person_by_card,is_person_by_category,count_she,count_he,count_they,count_nonbinary):
    
    singular_pronoun_totals = [count_she,count_he,count_nonbinary]
    person_counts = [is_person_by_card,is_person_by_category]
    
    # 1 or fewer counts of pronouns
    if sum([count_she,count_he,count_they,count_nonbinary]) <= 1:
        return ['inconclusive','0_pronoun_cts']
    
    if sum(person_counts)==0:
        return ['entity','0_person_ct']

    if count_she > count_he:
        return ['female','she_ct_greater_he']

    if count_he > count_she:
        return ['male','he_ct_greater_she']
        
        if count_they > 1 and count_nonbinary >= 1:
            return ['non-binary','they_and_nonbinary_greater_1']
    else:
        return ['none','none']
