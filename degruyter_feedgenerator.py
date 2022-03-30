#!/usr/bin/env python
# coding: utf-8


import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import csv
from lxml import etree

def dg2rss(key):
    url = f"https://www.degruyter.com/journal/key/{key}/html"
    page = requests.get(url)
    hostname = urlparse(url).hostname
    soup = BeautifulSoup(page.content)
    # Timestamp
    last_change = soup.find("h3","latestIssuePubDate").text.strip()
    last_change = datetime.strptime(last_change, '%B %Y').ctime()
    # Channel title
    channel_title = soup.title.text
    items = []
    for div in soup.find_all('div', attrs = {'id' : 'latestIssue'}):
        for article in div.find_all('div', attrs = {'class' : 'issueArticle'}):
            for resultTitle in article.find_all("div", "resultTitle"):
                link = f"https://{hostname}{resultTitle.a.get('href')}"
                title = resultTitle.h2.text.strip()
                items.append({
                    'title' : title,
                    'link' : link
                })
    root = etree.Element("rss", version = "2.0")
    channel = etree.SubElement(root,"channel")
    CH_TIT = etree.SubElement(channel, "title")
    CH_TIT.text = channel_title
    CH_link = etree.SubElement(channel, "link")
    CH_link.text = hostname
    CH_desc = etree.SubElement(channel, "description")

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

# with open('dg_journals.csv', 'r') as IN:
#     reader = csv.DictReader(IN)
#     for r in reader:
#         key = r.get('key')
#         dg2rss(key)
        

import pandas as pd
import time

fileurl = r'https://degruyter-live-craftcms-assets.s3.amazonaws.com/docs/titlelists/DG_Journals_2022_Paid_Access_EUR.xlsx'

df = pd.read_excel(fileurl, skiprows=3)
filtered_df = df[["Object", "Title", "Print - ISSN", "Online - ISSN", "Subject(s)", "DOI or URL"]]
filtered_df["key"] = filtered_df["DOI or URL"].str.replace('http\S+/','', regex = True).str.strip()
for index,row in filtered_df.iterrows():
    try:
        dg2rss(row["key"])
        filtered_df.loc[index, "rss_feed"] = f"https://raw.githubusercontent.com/alexander-winkler/degruyter_rss/main/feed/{row['key']}.xml"
    except Exception as e:
        print(e)
    time.sleep(0.4)

filtered_df.to_csv("feed_list.csv", index=None)