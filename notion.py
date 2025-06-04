import csv
import requests
from datetime import datetime
from env import NOTION_TOKEN, PARENT_PAGE_ID

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# === 创建当天的 Notion 页面（如 Papers_20250604） ===
def create_page_for_day(today_str):
    page_title = f"Papers_{today_str}"
    payload = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
        "properties": {
            "title": [{"type": "text", "text": {"content": page_title}}]
        },
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=payload)
    if response.status_code != 200:
        raise Exception(f"❌ Failed to create page: {response.text}")

    page_id = response.json()["id"]
    print(f"✅ Created Notion page: {page_title}")
    return page_id


# === 在指定页面下创建数据库 ===
def create_daily_database(parent_page_id, today_str):
    title = f"Papers_{today_str}"

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": {
            "Title": {"title": {}},
            "Model_Type": {"select": {"options": []}},
            "HHH_Focus": {"multi_select": {"options": []}},
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
    database_id = r.json()["id"]
    print(f"✅ Created Notion database inside page: {title}")
    return database_id


# === 上传 CSV 行到数据库 ===
def upload_csv_to_database(csv_path, database_id):
    with open(csv_path, newline='', encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            page = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Title": {"title": [{"text": {"content": row["Title"][:200]}}]},
                    "Authors": {"rich_text": [{"text": {"content": row["Authors"]}}]},
                    "Published": {"date": {"start": row["Published"]}},
                    "One_Sentence_Summary": {"rich_text": [{"text": {"content": row.get("One_Sentence_Summary", "")[:1000]}}]},
                    "Link": {"url": row["Link"]},
                    "Abstract_EN": {"rich_text": [{"text": {"content": row["Abstract_EN"][:2000]}}]},
                    "Abstract_ZH": {"rich_text": [{"text": {"content": row["Abstract_ZH"][:2000]}}]},
                    "Model_Type": {"select": {"name": row.get("Model_Type", "Unknown")}},
                    "HHH_Focus": {
                        "multi_select": [{"name": tag.strip()} for tag in row.get("HHH_Focus", "").split(",") if tag.strip()]
                    },
                    "Keywords": {
                        "multi_select": [{"name": k.strip()} for k in row.get("Keywords", "").split(",") if k.strip()]
                    },
                }
            }
            r = requests.post("https://api.notion.com/v1/pages", headers=NOTION_HEADERS, json=page)
            if r.status_code != 200:
                print(f"❌ Failed to upload row: {row['Title']}")
                print("Error:", r.text)
            else:
                print(f"✅ Uploaded: {row['Title']}")


def append_blocks_to_page(page_id, papers):
    blocks = []

    for paper in papers:
        title = paper["Title"]
        title = title.replace("\n", "").replace("\r", "").strip()
        authors = paper["Authors"]
        link = paper["Link"]
        published = paper["Published"]
        one_sentence_summary = paper.get("One_Sentence_Summary", "")
        keywords = paper.get("Keywords", "")
        hhh_focus = paper.get("HHH_Focus", "")
        abstract = paper.get("Abstract_EN", "")
        zh_abstract = paper.get("Abstract_ZH", "")

        # 标题块（加粗）
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"📄 {title}"},
                    "annotations": {"bold": True}
                }]
            }
        })

        # 普通段落块（不加粗）
        info_sections = [
            f"✍️ Authors: {authors}",
            f"📅 Published: {published}",
            f"📝 One Sentence Summary: {one_sentence_summary}",
            f"🧠 Keywords: {keywords}",
            f"🎯 Focus: {hhh_focus}",
        ]
        for info in info_sections:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": info[:2000]}
                    }]
                }
            })

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": { "content": "🔗 Link: " },
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": link,
                            "link": { "url": link }
                        },
                        "annotations": { "color": "blue" }
                    }
                ]
            }
        })

        # Abstract EN
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Abstract (EN):\n"},
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": abstract[:1900]}
                    }
                ]
            }
        })

        # Abstract ZH
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Abstract (ZH):\n"},
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": zh_abstract[:1900]}
                    }
                ]
            }
        })

        # Divider
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

    # 分批上传（每批不超过 50 blocks）
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(0, len(blocks), 50):
        chunk = blocks[i:i + 50]
        r = requests.patch(url, headers=NOTION_HEADERS, json={"children": chunk})
        if r.status_code != 200:
            print(f"❌ Failed to add blocks: {r.text}")
        else:
            print(f"✅ Added {len(chunk)} blocks.")


def upload_today_csv(csv_path=""):
    if not csv_path:
        print("❌ No CSV path provided. Please specify the path to your CSV file.")
        return
    
    today_str = datetime.now().strftime("%Y%m%d")

    print(f"\n📦 Processing CSV: {csv_path}")
    page_id = create_page_for_day(today_str)
    db_id = create_daily_database(page_id, today_str)

    # Read CSV once
    with open(csv_path, newline='', encoding="utf-8-sig") as f:
        papers = list(csv.DictReader(f))

    # Upload to database
    upload_csv_to_database(csv_path, db_id)

    # Also append human-readable blocks
    append_blocks_to_page(page_id, papers)

    print(f"\n🎉 All done! View your full page in Notion.")


if __name__ == "__main__":
    upload_today_csv("./archive/llm_alignment_papers_20240604.csv")  # 替换为实际的 CSV 文件路径
