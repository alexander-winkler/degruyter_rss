#!/usr/bin/env python
# coding: utf-8

# Import modules
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime, timezone
import uuid
import csv
from lxml import etree
import pandas as pd
import time

#############
# Functions ##
#############

def createTimestamp():
    iso_now = datetime.now(timezone.utc).isoformat()
    return iso_now

def generateUUID():
    generated_uuid = str(uuid.uuid4())
    return generated_uuid

def getLatestIssue(key:str):
    '''
    Function takes the de gruyter journal key,
    scrapes the journal website to get the URL of latest issue
    '''

    url = f"https://www.degruyterbrill.com/journal/key/{key}/html"
    # Download journal website
    page = requests.get(url)
    parsed_uri = urlparse(url)
    soup = BeautifulSoup(page.content, features = 'html.parser')
    
    # Get latest issue
    latestIssueLink = soup.find("a", id = "view-latest-issue")
    latestIssue = latestIssueLink['href'] if latestIssueLink else None

    # Journal Title
    title = soup.title.string if soup.title else "title not available"

    return title,f"{parsed_uri.scheme}://{parsed_uri.hostname}{latestIssue}"

def parseIssuePage(url):
    page = requests.get(url)
    parsed_uri = urlparse(url)
    soup = BeautifulSoup(page.content, features = 'html.parser')
    issueTitle = title = soup.title.string if soup.title else "issue title not available"

    itemList = soup.select('ul.issue-content-list li')

    issueItems = []

    for li in itemList:
        a_tag = li.find('a', class_='text-dark', attrs={'data-doi': True, 'href': True})
        title_span = li.find('span', class_='text-dark ahead-of-print-title')
        details_div = li.find('div', class_='ahead-of-print-details')
        if a_tag and details_div:
            item = {
                'doi': a_tag.get('data-doi'),
                'href': f"{parsed_uri.scheme}://{parsed_uri.hostname}{a_tag.get('href')}",
                'title': title_span.get_text(strip=True) if title_span else None,
                'date': details_div.find('div', class_='date').get_text(strip=True) if details_div.find('div', class_='date') else None,
                'authors': details_div.find('div', class_='authors').get_text(strip=True) if details_div.find('div', class_='authors') else None,
                'page_range': details_div.find('span', class_='pageRange').get_text(strip=True) if details_div.find('span', class_='pageRange') else None
            }
            issueItems.append(item)
    
    return issueTitle, issueItems

def IsLocalFeedOlder(key, mostRecentIssue):
    '''
    Checks if local via link is different from
    most recent issue online. If true, download
    new one 
    '''
    ns = { "atom" : 'http://www.w3.org/2005/Atom'}
    tree = etree.parse(f"feed/{key}.xml")
    lastUrlInFeed = tree.xpath('./atom:link[@rel = "via"]/@href', namespaces = ns)
    if len(lastUrlInFeed) > 0:
        if lastUrlInFeed[0].strip() == mostRecentIssue.strip():
            return False
        else:
            return True
    # If no valid link is found trigger download
    else:
        return True
        
    
def generateFeed(key, journalTitle, journalUrl, issueTitle, issueItems):

    # Create rss feed
    nsmap = {None: "http://www.w3.org/2005/Atom"}

    root = etree.Element("feed", nsmap = nsmap)
    
    # Channel info
    CH_TIT = etree.SubElement(root, "title")
    CH_TIT.text = journalTitle
    
    CH_link = etree.SubElement(root, "link", href = journalUrl, rel = "via")
    CH_feedLink = etree.SubElement(root,
    "link",
    href = f"https://raw.githubusercontent.com/alexander-winkler/degruyter_rss/main/feed/{key}.xml",
    type = "application/rss+xml",
    rel="self")

    CH_viaLink = etree.SubElement(root,
    "link",
    href = f"https://www.degruyterbrill.com/journal/key/{key}/html",
    rel="related")
    
    CH_timestamp = etree.SubElement(root, "updated")
    CH_timestamp.text = createTimestamp()

    # CH_author = etree.SubElement(root, "author")
    # CH_authName = etree.SubElement(CH_author, "name")
    # CH_authName.text = "Alexander Winkler"
    # CH_URI = etree.SubElement(CH_author, "uri")
    # CH_URI.text = "https://orcid.org/0000-0002-9145-7238"

    CH_id = etree.SubElement(root, "id")
    CH_id.text = f"https://raw.githubusercontent.com/alexander-winkler/degruyter_rss/main/feed/{key}.xml"
    
    CH_generator = etree.SubElement(root, "generator")
    CH_generator.text = "https://github.com/alexander-winkler/degruyter_rss/blob/main/degruyter_feedgenerator.py"
    
    CH_desc = etree.SubElement(root, "subtitle")
    CH_desc.text = f"A RSS feed containing the latest articles published in {journalTitle}"


    # Single items (articles)

    for i in issueItems:
        tmpItem = etree.SubElement(root, "entry")
        tmpTitle = etree.SubElement(tmpItem, "title")
        tmpTitle.text = i.get('title')
        tmpLink = etree.SubElement(tmpItem, 'link', href = i.get('href'))
        tmpID = etree.SubElement(tmpItem, 'id')
        tmpID.text = "https://doi.org/" + i.get('doi')
        tmpUpdate = etree.SubElement(tmpItem, 'updated')
        tmpUpdate.text = createTimestamp()
        tmpDescription = etree.SubElement(tmpItem, 'summary')
        tmpDescription.text = "DOI: https://doi.org/" + i.get('doi')
        if i.get('authors'):
            tmpDescription.text = "Article by " + i.get('authors') + "\n" + tmpDescription.text
  
    tree = etree.ElementTree(root)
    tree.write(f'feed/{key}.xml', pretty_print=True, xml_declaration=True,   encoding="UTF-8", standalone = True)
    print(f"{key} done!")

def workflow(key):
    journalTitle, journalUrl = getLatestIssue(key)
    if IsLocalFeedOlder(key, journalUrl) == True:
        issueTitle, issueItems = parseIssuePage(journalUrl)
        generateFeed(key, journalTitle, journalUrl, issueTitle, issueItems)
    else:
        print(f"{journalTitle} ({key}) is up to date!")

def getKeyList(file):
    df = pd.read_excel(fileurl, skiprows=3)

def processFile(file):
    # read excel file into a dataframe, select columns that are needed
    df = pd.read_excel(fileurl, skiprows=3)
    filtered_df = df[["Journal Code Klopotek", "Journal Code Online", "Title", "Print-ISSN", "Online-ISSN", "Subject Area", "URL"]].copy()

    # run function on keys
    for index,row in filtered_df.iterrows():
        try:
            workflow(row["Journal Code Online"])
            filtered_df.loc[index, "rss_feed"] = f"https://raw.githubusercontent.com/alexander-winkler/degruyter_rss/main/feed/{row['Journal Code Online']}.xml"
        except Exception as e:
            print(e)
        time.sleep(1)

    # Finally, write a csv list of feeds generated

    filtered_df.to_csv("feed_list.csv", index=None)

if __name__ == "__main__":
     
    # The journal keys derive from the official price list De Gruyter has on its website (will probably change in the near future, so that's not a particularly good idea)
    fileurl = r'https://degruyter-live-craftcms-assets.s3.amazonaws.com/docs/DeGruyter_Journal_Price_List_2025__EUR__2024-11-10.xlsx'
    processFile(fileurl)