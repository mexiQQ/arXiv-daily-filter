import requests
import json
import csv
from time import sleep
from datetime import datetime
from backdoor_slack import send_slack_message, send_slack_banner, send_slack_compressed_message
from env import SLACK_WEBHOOK_URL_GROUP, SLACK_WEBHOOK_URL_MY_GROUP2, SLACK_WEBHOOK_URL_MY, SLACK_WEBHOOK_URL_Prof
from fetch import fetch_arxiv_metadata, parse_arxiv_feed
from backdoor_notion import upload_today_csv


# === 模型配置 ===
API_URL = "http://localhost:8000/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer token"
}
MODEL = "mistralai/Mistral-Small-24B-Instruct-2501"

# === 构造 Prompt ===
def build_backdoor_prompt(title, summary):
    return f"""You are an AI research assistant.

Given the following paper title and abstract, determine if the paper is related to backdoor techniques in large language models (LLMs) or large multimodal models (LMMs). (Please note it should be related to **backdoor** technique first)

If the paper is related, respond in this format:

Yes  
Explanation: <why it's relevant>  
Model Type: <LLM or LMM>  
Use Intention: <Positive or Negative>  
Focus: <Attack, Defense, or Both>  
Keywords: <3–5 keywords>  
Chinese Abstract: <Translate abstract into Chinese>  
One Sentence Summary: <Concise English summary>

If not related, respond:
No

Title: {title}

Abstract: {summary}
"""

# === 调用模型 ===
def query_mistral(prompt):
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Always respond clearly and concisely."},
        {"role": "user", "content": prompt}
    ]
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.0,
        "top_p": 1.0,
        "top_k": -1
    }
    response = requests.post(API_URL, headers=HEADERS, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# === 主逻辑 ===
if __name__ == "__main__":
    print("🔍 Fetching arXiv backdoor papers...")
    xml_data = fetch_arxiv_metadata("cat:cs.AI OR cat:cs.CL OR cat:cs.CV OR cat:cs.CY OR cat:cs.CR OR cat:cs.LG")
    papers = parse_arxiv_feed(xml_data)

    print(f"✅ Fetched {len(papers)} papers.")

    results = []
    for i, paper in enumerate(papers, start=1):
        print(f"\n--- Processing Paper {i} ---")
        print("Title:", paper['title'])
        print("Summary (EN):", paper['summary'][:300], "...")

        prompt = build_backdoor_prompt(paper['title'], paper['summary'])
        try:
            result = query_mistral(prompt)
        except Exception as e:
            print(f"❌ Request failed: {e}")
            continue

        lines = [line.strip() for line in result.splitlines() if line.strip()]
        if lines and lines[0].lower() == "yes":
            data = {
                "Title": paper['title'],
                "Authors": ", ".join(paper['authors']),
                "Published": paper['published'],
                "Link": paper['pdf_url'],
                "Abstract_EN": paper['summary'],
                "Abstract_ZH": "",
                "One_Sentence_Summary": "",
                "Model_Type": "",
                "Use_Intention": "",
                "Focus": "",
                "Keywords": ""
            }
            for line in lines[1:]:
                if line.startswith("Explanation:"): continue
                elif line.startswith("Model Type:"):
                    data["Model_Type"] = line.replace("Model Type:", "").strip()
                elif line.startswith("Use Intention:"):
                    data["Use_Intention"] = line.replace("Use Intention:", "").strip()
                elif line.startswith("Focus:"):
                    data["Focus"] = line.replace("Focus:", "").strip()
                elif line.startswith("Keywords:"):
                    data["Keywords"] = line.replace("Keywords:", "").strip()
                elif line.startswith("Chinese Abstract:"):
                    data["Abstract_ZH"] = line.replace("Chinese Abstract:", "").strip()
                elif line.startswith("One Sentence Summary:"):
                    data["One_Sentence_Summary"] = line.replace("One Sentence Summary:", "").strip()
                else:
                    data["Abstract_ZH"] += "\n" + line

            results.append(data)
            print("✅ Related to backdoor.")
            break
        else:
            print("🚫 Not backdoor related.")

        sleep(1)

    # === 保存 CSV ===
    today_str = datetime.now().strftime('%Y%m%d')
    csv_file = f"./archive/llm_backdoor_papers_{today_str}.csv"
    fieldnames = [
        "Title", "Authors", "Published", "Link",
        "Abstract_EN", "Abstract_ZH", "One_Sentence_Summary",
        "Model_Type", "Use_Intention", "Focus", "Keywords"
    ]
    with open(csv_file, "w", newline='', encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"\n✅ Saved {len(results)} relevant papers to {csv_file}")

    # === 上传到 Notion 数据库 ===
    notion_database_id = upload_today_csv(csv_file)

    # === 发送 Slack 通知（可选） ===
    send_slack_banner(SLACK_WEBHOOK_URL_MY_GROUP2)
    try:
        send_slack_message(paper, SLACK_WEBHOOK_URL_MY_GROUP2)
    except Exception as e:
        print(f"❌ Failed to send Slack message: {e}")

    # === 发送 Slack 压缩消息 ===
    send_slack_compressed_message(results, SLACK_WEBHOOK_URL_MY)
    send_slack_compressed_message(results, SLACK_WEBHOOK_URL_Prof)
    # send_slack_compressed_message(results, SLACK_WEBHOOK_URL_GROUP)
 
