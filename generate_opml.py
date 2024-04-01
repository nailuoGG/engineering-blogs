from termcolor import colored
import re
import requests
import json
from bs4 import BeautifulSoup

OUTPUT_FILENAME = "engineering_blogs.opml"
JSON_FILENAME = "engineering_blogs.json"
TITLE = "Engineering Blogs"


class Blog:
    def __init__(self, name, web_url, rss_url, desc=None, tags=None):
        self.name = name
        self.web_url = web_url
        self.rss_url = rss_url
        self.desc = desc
        self.tags = tags


def get_rss_url_from_inoreader(web_url):
    rss_check_url = (
        f"https://www.inoreader.com/autocomplete.php?term={web_url}&origin=smart_search"
    )
    response = requests.get(rss_check_url)
    data = json.loads(response.text)
    for item in data:
        if "type" in item and item["type"] == "feed":
            return item["value"]
    return None


def get_rss_url_from_feedly(web_url):
    rss_check_url = f"https://cloud.feedly.com/v3/search/feeds/?query={web_url}"
    response = requests.get(rss_check_url)
    data = json.loads(response.text)
    if "results" in data:
        for result in data["results"]:
            if "feedId" in result:
                return result["feedId"].replace("feed/", "")
    return None


def get_rss_url(web_url):
    rss_url = get_rss_url_from_inoreader(web_url)
    if rss_url is None:
        rss_url = get_rss_url_from_feedly(web_url)
    return rss_url


def get_blogs_from_readme():
    with open("README.md", "r") as readme:
        contents = readme.read()
    matches = re.findall(r"\* (.*) (http.*)", contents)
    return matches


def get_existing_blogs_from_opml():
    existing_blogs = {}
    try:
        with open(OUTPUT_FILENAME, "r") as file:
            soup = BeautifulSoup(file, "lxml")
            outlines = soup.find_all("outline")
            for outline in outlines:
                if "htmlurl" in outline.attrs and "xmlurl" in outline.attrs:
                    existing_blogs[outline["htmlurl"]] = outline["xmlurl"]
    except FileNotFoundError:
        pass
    return existing_blogs


def write_blogs_to_opml(blogs):
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


def write_blogs_to_json(blogs):
    blogs_json = []
    for blog in blogs:
        blogs_json.append(
            {
                "title": blog.name,
                "desc": blog.desc,
                "site_url": blog.web_url,
                "rss_url": blog.rss_url,
                "tags": blog.tags,
            }
        )
    with open(JSON_FILENAME, "w") as json_file:
        json.dump(blogs_json, json_file, indent=4)


def main():
    blogs = []
    unavailable = []
    existing_blogs = get_existing_blogs_from_opml()
    for match in get_blogs_from_readme():
        name, web_url = match
        rss_url = existing_blogs.get(web_url)
    for match in get_blogs_from_readme():
        name, web_url = match
        rss_url = existing_blogs.get(web_url)
        if rss_url is None:
            rss_url = get_rss_url(web_url)
            print(colored(f"SMART SEARCH: Rss Feed: {rss_url}", "green"))
        else:
            print(colored(f"ALREADY HAVE: Rss Feed: {rss_url}", "yellow"))
        if rss_url:
            blogs.append(Blog(name, web_url, rss_url))
        else:
            unavailable.append(Blog(name, web_url, rss_url))
            print(colored(f"UNABLE FIND: Rss Feed for: {web_url}", "red"))
    blogs.sort(key=lambda b: b.name.capitalize())
    unavailable.sort(key=lambda b: b.name.capitalize())
    write_blogs_to_opml(blogs)
    write_blogs_to_json(blogs)
    print(f"DONE: {len(blogs)} written to {OUTPUT_FILENAME} and {JSON_FILENAME}")


if __name__ == "__main__":
    main()
