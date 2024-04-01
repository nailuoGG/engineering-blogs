import re
import requests
import json
from bs4 import BeautifulSoup

OUTPUT_FILENAME = "engineering_blogs.opml"
TITLE = "Engineering Blogs"

# grab name/url pairings from README.md
with open("README.md", "r") as readme:
    contents = readme.read()
matches = re.findall(r"\* (.*) (http.*)", contents)

# skip over blogs that aren't found
unavailable = []
fast_forwards = [
    "Baidu Research",
    "Booking.com",
    "Fynd",
    "Graphcool",
    "LinkedIn",
    "Medallia",
    "OmniTI",
    "Paperless Post",
    "Pluralsight",
    "Prolific Interactive",
    "Quora",
    "Robert Elder Software",
    "Simple",
    "SlideShare",
    "SourceClear",
    "Viget",
    "Zalando",
    "Zapier",
    "Zynga",
    "Dave Beazley",
    "Edan Kwan",
    "Grzegorz Gajos",
    "Joe Armstrong",
    "Kai Hendry",
    "LiveOverflow",
]


class Blog:
    def __init__(self, name, web_url, rss_url):
        self.name = name
        self.web_url = web_url
        self.rss_url = rss_url


blogs = []

# for each blog URL, check if rss URL exists
for match in matches:
    name, web_url = match

    if name in fast_forwards:
        print(f"{name}: TEMP IGNORE")
        unavailable.append(Blog(name, web_url, None))
        continue

    # if rss_url already in existing opml file, use that; otherwise, do a lookup
    rss_url = None
    try:
        with open(OUTPUT_FILENAME, "r") as file:
            soup = BeautifulSoup(file, "lxml")
            existing_blog = soup.find("outline", {"htmlurl": web_url})
            if existing_blog:
                rss_url = existing_blog["xmlurl"]
                print(f"{name}: ALREADY HAVE")
    except FileNotFoundError:
        pass

    if rss_url is None:
        print(f"{name}: GETTING")
        rss_check_url = f"https://www.inoreader.com/autocomplete.php?term={web_url}&origin=smart_search"
        response = requests.get(rss_check_url)
        data = json.loads(response.text)
        for item in data:
            if "type" in item and item["type"] == "feed":
                rss_url = item["value"]
                print(rss_url)
                break

    if rss_url:
        blogs.append(Blog(name, web_url, rss_url))
    else:
        unavailable.append(Blog(name, web_url, rss_url))

blogs.sort(key=lambda b: b.name.capitalize())
unavailable.sort(key=lambda b: b.name.capitalize())

# create and write to opml file
soup = BeautifulSoup(features="xml")
opml = soup.new_tag("opml", version="1.0")
soup.append(opml)

head = soup.new_tag("head")
title = soup.new_tag("title")
title.string = TITLE
head.append(title)
opml.append(head)

body = soup.new_tag("body")
outline = soup.new_tag("outline", text=TITLE, title=TITLE)
body.append(outline)
opml.append(body)

for blog in blogs:
    outline.append(
        soup.new_tag(
            "outline",
            type="rss",
            text=blog.name,
            title=blog.name,
            xmlUrl=blog.rss_url,
            htmlUrl=blog.web_url,
        )
    )

with open(OUTPUT_FILENAME, "w") as file:
    file.write(str(soup.prettify()))

print(f"DONE: {len(blogs)} written to {OUTPUT_FILENAME}")

print("\nUnable to find an RSS feed for the following blogs:")
print("===================================================")
for b in unavailable:
    print(f"{b.name} | {b.web_url}")
print("===================================================")
