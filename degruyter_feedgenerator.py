#!/usr/bin/env python
# coding: utf-8

# Import modules
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import csv
from lxml import etree
import pandas as pd
import time

#############
# Function ##
#############

def dg2rss(key:str):
    '''
    Function takes the de gruyter journal key,
    scrapes the journal website to get some info on articles,
    eventually writes an rss-xml-file for each journal.
    '''

    url = f"https://www.degruyter.com/journal/key/{key}/html"
    
    # Download journal website
    page = requests.get(url)
    hostname = urlparse(url).hostname
    soup = BeautifulSoup(page.content, features = 'html.parser')
    
    # Timestamp
    last_change = soup.find("h3","latestIssuePubDate").text.strip()
    last_change = datetime.strptime(last_change, '%B %Y').ctime()
    
    # Journal titel (will become channel title in rss)
    channel_title = soup.title.text
    items = []
    
    # Populate items list with info on articles

    for div in soup.find_all('div', attrs = {'id' : 'latestIssue'}):
        for article in div.find_all('div', attrs = {'class' : 'issueArticle'}):
            for resultTitle in article.find_all("div", "resultTitle"):
                link = f"https://{hostname}{resultTitle.a.get('href')}"
                title = resultTitle.h2.text.strip()
                items.append({
                    'title' : title,
                    'link' : link
                })

    # Create rss feed
    root = etree.Element("rss", version = "2.0")

    # Channel info
    channel = etree.SubElement(root,"channel")
    CH_TIT = etree.SubElement(channel, "title")
    CH_TIT.text = channel_title
    CH_link = etree.SubElement(channel, "link")
    CH_link.text = hostname
    CH_desc = etree.SubElement(channel, "description")

    # Single items (articles)
    for i in items:
        tmpItem = etree.SubElement(channel, "item")
        tmpTitle = etree.SubElement(tmpItem, "title")
        tmpTitle.text = i.get('title')
        tmpLink = etree.SubElement(tmpItem, 'link')
        tmpLink.text = i.get('link')
        guid = etree.SubElement(tmpItem, 'guid')
        guid.text = i.get('link')
    tree = etree.ElementTree(root)
    tree.write(f'feed/{key}.xml', pretty_print=True, xml_declaration=True,   encoding="UTF-8", standalone = True)
    print(f"{key} done!")


######################
#### script proper ###
######################

# The journal keys derive from the official price list De Gruyter has on its website (will probably change in the near future, so that's not a particularly good idea)

fileurl = r'https://degruyter-live-craftcms-assets.s3.amazonaws.com/docs/titlelists/DG_Journals_2022_Paid_Access_EUR.xlsx'

# read excel file into a dataframe, select columns that are needed

df = pd.read_excel(fileurl, skiprows=3)
filtered_df = df[["Object", "Title", "Print - ISSN", "Online - ISSN", "Subject(s)", "DOI or URL"]]
# keys are implicit in the url present in the spreadsheet
filtered_df.loc[:, "key"] = filtered_df["DOI or URL"].str.replace('http\S+/','', regex = True).str.strip()

# run function on keys
for index,row in filtered_df.iterrows():
    try:
        dg2rss(row["key"])
        filtered_df.loc[index, "rss_feed"] = f"https://raw.githubusercontent.com/alexander-winkler/degruyter_rss/main/feed/{row['key']}.xml"
    except Exception as e:
        print(e)
    time.sleep(0.4)

# Finally, write a csv list of feeds generated

filtered_df.to_csv("feed_list.csv", index=None)

# Some keys apparently are not contained in the 'filurl` file above.
# Therefore, add a simple key list file in `additional_keys.csv` to be added.

try:
    with open('additional_keys.csv', 'r') as IN:
        print("additional keys found with following keys:")
        for key in IN.read().split('\n'):
            key = key.strip()
            print(f"\t- {key}")
            dg2rss(key)
except Exception as e:
    print(e)