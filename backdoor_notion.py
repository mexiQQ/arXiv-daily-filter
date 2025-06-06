import csv
import requests
from datetime import datetime
from env import NOTION_TOKEN, BACKDOOR_PARENT_PAGE_ID

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def create_page_for_day(today_str):
    title = f"Backdoor_Papers_{today_str}"
    payload = {
        "parent": {"type": "page_id", "page_id": BACKDOOR_PARENT_PAGE_ID},
        "properties": {
            "title": [{"type": "text", "text": {"content": title}}]
        },
    }
    r = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
    if r.status_code != 200:
        raise Exception(f"❌ Failed to create page: {r.text}")
    page_id = r.json()["id"]
    print(f"✅ Created Notion page: {title}")
    return page_id


def create_daily_database(BACKDOOR_PARENT_PAGE_ID, today_str):
    title = f"Backdoor_Papers_{today_str}"
    payload = {
        "parent": {"type": "page_id", "page_id": BACKDOOR_PARENT_PAGE_ID},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": {
            "Title": {"title": {}},
            "Model_Type": {"select": {"options": []}},
            "Use_Intention": {"select": {"options": []}},  # Positive / Negative
            "Focus": {"multi_select": {"options": []}},    # Attack / Defense / Both
            "Keywords": {"multi_select": {"options": []}},
            "Link": {"url": {}},
            "Published": {"date": {}},
            "One_Sentence_Summary": {"rich_text": {}},
            "Authors": {"rich_text": {}},
            "Abstract_EN": {"rich_text": {}},
            "Abstract_ZH": {"rich_text": {}},
        }
    }
    r = requests.post("https://api.notion.com/v1/databases", headers=NOTION_HEADERS, json=payload)
    if r.status_code != 200:
        raise Exception(f"❌ Failed to create database: {r.text}")
    print(f"✅ Created Notion database: {title}")
    return r.json()["id"]


def upload_csv_to_database(csv_path, database_id):
    with open(csv_path, newline='', encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Title": {"title": [{"text": {"content": row["Title"].replace("\n", "").replace("\r", "").strip()[:200]}}]},
                    "Authors": {"rich_text": [{"text": {"content": row["Authors"]}}]},
                    "Published": {"date": {"start": row["Published"]}},
                    "One_Sentence_Summary": {"rich_text": [{"text": {"content": row.get("One_Sentence_Summary", "")[:1000]}}]},
                    "Link": {"url": row["Link"]},
                    "Abstract_EN": {"rich_text": [{"text": {"content": row["Abstract_EN"][:2000]}}]},
                    "Abstract_ZH": {"rich_text": [{"text": {"content": row["Abstract_ZH"][:2000]}}]},
                    "Model_Type": {"select": {"name": row.get("Model_Type", "Unknown")}},
                    "Use_Intention": {"select": {"name": row.get("Use_Intention", "Unknown")}},
                    "Focus": {
                        "multi_select": [{"name": f.strip()} for f in row.get("Focus", "").split(",") if f.strip()]
                    },
                    "Keywords": {
                        "multi_select": [{"name": k.strip()} for k in row.get("Keywords", "").split(",") if k.strip()]
                    },
                }
            }
            r = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=data)
            if r.status_code != 200:
                print(f"❌ Failed to upload: {row['Title']}")
                print("Error:", r.text)
            else:
                print(f"✅ Uploaded: {row['Title']}")


def append_blocks_to_page(page_id, papers):
    blocks = []

    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text",
                "text": {"content": f"📄 Total {len(papers)} backdoor-related papers today"},
                "annotations": {"bold": True}
            }]
        }
    })

    blocks.append({"object": "block", "type": "divider", "divider": {}})

    for paper in papers:
        title = paper["Title"].replace("\n", "").replace("\r", "").strip()
        authors = paper["Authors"]
        published = paper["Published"]
        summary = paper.get("One_Sentence_Summary", "")
        keywords = paper.get("Keywords", "")
        use = paper.get("Use_Intention", "")
        focus = paper.get("Focus", "")
        link = paper.get("Link", "")
        en = paper.get("Abstract_EN", "")
        zh = paper.get("Abstract_ZH", "")

        blocks.extend([
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"📌 {title}"},
                        "annotations": {"bold": True}
                    }]
                }
            },
            *[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": info[:2000]}
                        }]
                    }
                }
                for info in [
                    f"✍️ Authors: {authors}",
                    f"📅 Published: {published}",
                    f"🧠 Keywords: {keywords}",
                    f"🚦 Intention: {use}",
                    f"🎯 Focus: {focus}",
                    f"📝 Summary: {summary}"
                ]
            ],
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "🔗 Link: "}, "annotations": {"bold": True}},
                        {"type": "text", "text": {"content": link, "link": {"url": link}}, "annotations": {"color": "blue"}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Abstract (EN):\n"}, "annotations": {"bold": True}},
                        {"type": "text", "text": {"content": en[:1900]}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Abstract (ZH):\n"}, "annotations": {"bold": True}},
                        {"type": "text", "text": {"content": zh[:1900]}}
                    ]
                }
            },
            {"object": "block", "type": "divider", "divider": {}}
        ])

    for i in range(0, len(blocks), 50):
        chunk = blocks[i:i + 50]
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        r = requests.patch(url, headers=NOTION_HEADERS, json={"children": chunk})
        if r.status_code != 200:
            print(f"❌ Block upload error: {r.text}")
        else:
            print(f"✅ Uploaded {len(chunk)} blocks")


def upload_today_csv(csv_path=""):
    if not csv_path:
        print("❌ CSV path missing.")
        return
    today_str = datetime.now().strftime("%Y%m%d")
    page_id = create_page_for_day(today_str)
    db_id = create_daily_database(page_id, today_str)

    with open(csv_path, newline='', encoding="utf-8-sig") as f:
        papers = list(csv.DictReader(f))

    upload_csv_to_database(csv_path, db_id)
    append_blocks_to_page(page_id, papers)
    print("🎉 Done. View in Notion.")


if __name__ == "__main__":
    upload_today_csv("./archive/backdoor_llm_papers_20250604.csv")  # 替换为实际文件路径
