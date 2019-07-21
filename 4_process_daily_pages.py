from __future__ import print_function
import boto3
import csv
import datetime
import io
import pandas as pd
import sys
from src import scraping
from src import data

# intialize connection to S3 resources
s3 = boto3.resource('s3')
s3_client = boto3.client('s3', 'us-east-1')

output = 's3'
bucket = 'afd-scraped'

def lambda_handler(event, context):
    
    yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
    
    # extract list of keys for indiv_afd_analysis files saved yetesrday
    keys = data.get_keys_in_bucket(s3_client,bucket,'individual_afd_analysis/{}'.format(yesterday))
    
    # combine all indiv_afd_analysis into one csv
    master_df = pd.DataFrame()
    for k in keys:
        df = data.read_csv_on_s3(s3_client,bucket,k)
        master_df = data.append_dataframes(master_df,df)
    
    master_df['is_person_by_card'] = master_df['is_person_by_card'].fillna(0)
    master_df['is_person_by_category'] = master_df['is_person_by_category'].fillna(0)

    
    master_df['select_gender_identity'] = master_df[['is_person_by_card','is_person_by_category',
                                                     'count_she','count_he','count_they','count_nonbinary']].apply(lambda x: data.select_gender_identity(x[0],x[1],x[2],x[3],x[4],x[5]),axis=1 )
    master_df['recommended_gender'] = master_df['select_gender_identity'].apply(lambda x: x[0])
    master_df['gender_rule'] = master_df['select_gender_identity'].apply(lambda x: x[1])
    master_df = master_df.drop("select_gender_identity",axis=1)
    
    resultsString = master_df.to_csv( quoting=csv.QUOTE_NONNUMERIC,index=False)
    scraping.store_string(resultsString, "daily_afd_analysis")
