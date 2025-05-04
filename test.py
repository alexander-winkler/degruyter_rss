from degruyter_feedgenerator import getLatestIssue, parseIssuePage, generateFeed, workflow

key = "bd"

try:
    name, url = getLatestIssue(key)
    print(name, url)
    print("latest issue could be retrieved")
except Exception as e:
    print(e)

try:
    issueTitle, issueItems = parseIssuePage(url)
    print(issueTitle, issueItems)
    print("issue page parsed sucessfully!")
except Exception as e:
    print(e)

try:
    generateFeed(key, name, url, issueTitle, issueItems)
except Exception as e:
    print(e)


try:
    workflow(key)
except Exception as e:
    print(e)