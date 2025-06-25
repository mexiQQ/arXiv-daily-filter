import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+

def get_previous_day_range_utc_for_la():
    la = ZoneInfo("America/Los_Angeles")
    now_la = datetime.now(la)
    yesterday = (now_la - timedelta(days=1)).date()

    start_la = datetime.combine(yesterday, datetime.min.time(), tzinfo=la)
    end_la = datetime.combine(yesterday, datetime.max.time(), tzinfo=la)

    start_utc = start_la.astimezone(ZoneInfo("UTC"))
    end_utc = end_la.astimezone(ZoneInfo("UTC"))

    return start_utc.strftime('%Y%m%d%H%M'), end_utc.strftime('%Y%m%d%H%M')

def get_previous_day_range_utc_for_ny():
    ny = ZoneInfo("America/New_York")
    now_ny = datetime.now(ny)
    yesterday = (now_ny - timedelta(days=3)).date()

    # 昨天纽约时间的 00:00 到 23:59
    start_ny = datetime.combine(yesterday, datetime.min.time(), tzinfo=ny)
    end_ny = datetime.combine(yesterday, datetime.max.time(), tzinfo=ny)

    # 转为 UTC
    start_utc = start_ny.astimezone(ZoneInfo("UTC"))
    end_utc = end_ny.astimezone(ZoneInfo("UTC"))

    return start_utc.strftime('%Y%m%d%H%M'), end_utc.strftime('%Y%m%d%H%M')

# === 构造 arXiv 查询 URL 并抓取 XML 数据
def fetch_arxiv_metadata_old(category="cat:cs.AI", max_results=2000):
    start_time, end_time = get_previous_day_range_utc_for_ny()
    base_url = "https://dailyarxiv.com/query.php"
    query = f"({category}) AND lastUpdatedDate:[{start_time} TO {end_time}]"
    print(f"🔍 Fetching arXiv metadata for query: {query}")
    params = {
        "search_query": query,
        "max_results": max_results
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return response.content

# === 解析 arXiv 的 Atom Feed，提取 Meta 信息
def parse_arxiv_feed_old(xml_data):
    namespace = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
    root = ET.fromstring(xml_data)
    papers = []
    for entry in root.findall('atom:entry', namespace):
        paper = {
            'id': entry.find('atom:id', namespace).text,
            'title': entry.find('atom:title', namespace).text.strip(),
            'summary': entry.find('atom:summary', namespace).text.strip(),
            'published': entry.find('atom:published', namespace).text,
            'updated': entry.find('atom:updated', namespace).text,
            'authors': [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)],
            'pdf_url': next((link.attrib['href'] for link in entry.findall('atom:link', namespace) if link.attrib.get('type') == 'application/pdf'), None)
        }
        papers.append(paper)
    return papers

def fetch_arxiv_metadata(category="cs.AI+cs.CL+cs.CV+cs.CY+cs.CR+cs.LG"):
    rss_url = f"https://rss.arxiv.org/rss/{category}"
    print(f"🔍 Fetching RSS feed from: {rss_url}")
    response = requests.get(rss_url)
    response.raise_for_status()
    return response.content

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

if __name__ == "__main__":
    xml_data = fetch_arxiv_metadata("cs.AI")
    papers = parse_arxiv_feed(xml_data)

    print(f"✅ Fetched {len(papers)} papers from arXiv cs.AI:")
    for i, paper in enumerate(papers[:3], start=1):  # 仅展示前3条
        print(f"\n--- Paper {i} ---")
        print("Title:", paper['title'])
        print("Authors:", ", ".join(paper['authors']))
        print("Published:", paper['published'])
        print("PDF:", paper['pdf_url'])
        print("Summary:", paper['summary'][:300], "...\n")  # 摘要只展示前300字


