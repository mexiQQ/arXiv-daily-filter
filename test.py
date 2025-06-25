import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

def parse_arxiv_feed(xml_data):
    ns = {
        'dc': 'http://purl.org/dc/elements/1.1/',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }

    root = ET.fromstring(xml_data)
    papers = []

    for item in root.findall('./channel/item'):
        pub_date_str = item.find('pubDate').text
        pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")

        # 提取作者
        creators = item.findall('dc:creator', ns)
        authors = [creator.text.strip() for creator in creators if creator.text]

        # 只保留 Abstract 后的内容
        description = item.find('description').text.strip()
        abstract = description.split("Abstract:", 1)[-1].strip() if "Abstract:" in description else description

        paper = {
            'id': item.find('guid').text.strip(),
            'title': item.find('title').text.strip(),
            'summary': abstract,
            'published': pub_date.isoformat(),
            'updated': pub_date.isoformat(),
            'authors': authors,
            'pdf_url': item.find('link').text.strip().replace('abs', 'pdf') + ".pdf"
        }
        papers.append(paper)

    return papers

def fetch_arxiv_rss(category="cs.AI"):
    rss_url = f"https://rss.arxiv.org/rss/{category}"
    print(f"🔍 Fetching RSS feed from: {rss_url}")
    response = requests.get(rss_url)
    response.raise_for_status()
    return response.content


xml_data = fetch_arxiv_rss("cs.AI+cs.CL+cs.CV+cs.CY+cs.CR+cs.LG")
papers = parse_arxiv_feed(xml_data)
for p in papers[:10]:
    print(p)
