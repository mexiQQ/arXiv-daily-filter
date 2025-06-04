import requests
import json
import csv
from time import sleep
from datetime import datetime
from slack import send_slack_message
from env import SLACK_WEBHOOK_URL_MY
from fetch import fetch_arxiv_metadata, parse_arxiv_feed

# === Mistral API 配置 ===
API_URL = "http://localhost:8000/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer token"
}
MODEL = "mistralai/Mistral-Small-24B-Instruct-2501"

# === 构造英文分类与翻译任务的 prompt
def build_prompt(title, summary):
    return f"""You are an AI research assistant.

Given a research paper title and abstract, determine if it is related to large language models (LLMs) or large language models (LLMs) Alignment (e.g., helpful, harmless, and honest). Please focus only on alignment of LLMs or LMMs, not general AI system such as robotics.

If the paper is related, return:
Yes
Explanation: <short explanation why it's related>
Model Type: <LLM or LMM>
HHH Focus: <Helpful, Harmless, Honest – list all that apply>
Keywords: <3–5 short keywords>
Chinese Abstract: <Translate the abstract into Chinese>
One Sentence Summary: <A concise one-sentence summary of the paper>

If the paper is not related, respond:
No

Title: {title}

Abstract: {summary}
"""

# === 调用本地 Mistral 模型进行分类和翻译
def query_mistral(prompt):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Always respond clearly and concisely."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    data = {"model": MODEL, "messages": messages, "temperature": 0.0, "top_p": 1.0, "top_k": -1}
    response = requests.post(API_URL, headers=HEADERS, data=json.dumps(data))
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# === 主执行流程
if __name__ == "__main__":
    print("🔍 Fetching arXiv papers...")
    xml_data = fetch_arxiv_metadata("cat:cs.AI OR cat:cs.CL OR cat:cs.CV OR cat:cs.CY OR cat:cs.CR OR cat:cs.LG")
    papers = parse_arxiv_feed(xml_data)

    # cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.CV+OR+cat:cs.CY+OR+cat:cs.CR+OR+cat:cs.LG
    results = []
    print(f"✅ Fetched {len(papers)} papers from arXiv cat:cs.AI OR cat:cs.CL OR cat:cs.CV OR cat:cs.CY OR cat:cs.CR OR cat:cs.LG.")

    for i, paper in enumerate(papers[:10], start=1):
        print(f"\n--- Processing Paper {i} ---")
        print("Title:", paper['title'])
        print("Authors:", ", ".join(paper['authors']))
        print("Published:", paper['published'])
        print("PDF:", paper['pdf_url'])
        print("Summary:", paper['summary'][:300], "...\n")  # 摘要只展示前300字

        prompt = build_prompt(paper['title'], paper['summary'])
        try:
            result = query_mistral(prompt)
        except Exception as e:
            print(f"❌ Request failed: {e}")
            continue

        lines = [line.strip() for line in result.strip().splitlines() if line.strip()]
        if lines and lines[0].lower() == "yes":
            explanation = model_type = hhh_focus = keywords = zh_translation = ""
            for line in lines[1:]:
                if line.startswith("Explanation:"):
                    explanation = line.replace("Explanation:", "").strip()
                elif line.startswith("Model Type:"):
                    model_type = line.replace("Model Type:", "").strip()
                elif line.startswith("HHH Focus:"):
                    hhh_focus = line.replace("HHH Focus:", "").strip()
                elif line.startswith("Keywords:"):
                    keywords = line.replace("Keywords:", "").strip()
                elif line.startswith("Chinese Abstract:"):
                    zh_translation = line.replace("Chinese Abstract:", "").strip()
                elif line.startswith("One Sentence Summary:"):
                    one_sentence_summary = line.replace("One Sentence Summary:", "").strip()
                else:
                    zh_translation += "\n" + line  # 处理多行翻译

            paper = {
                "Title": paper['title'],
                "Authors": ", ".join(paper['authors']),
                "Published": paper['published'],
                "Link": paper['pdf_url'],
                "Abstract_EN": paper['summary'],
                "Abstract_ZH": zh_translation.strip(),
                "One_Sentence_Summary": one_sentence_summary.strip(),
                "Model_Type": model_type,
                "HHH_Focus": hhh_focus,
                "Keywords": keywords
            }
            results.append(paper)

            # === 发送 Slack 通知（可选） ===
            try:
                send_slack_message(paper, SLACK_WEBHOOK_URL_MY)
            except Exception as e:
                print(f"❌ Failed to send Slack message: {e}")
        else:
            print("🚫 Not relevant")

        sleep(1)  # 避免过快请求

    # === 写入 CSV 文件 ===
    csv_file = f"./archive/llm_alignment_papers_{datetime.now().strftime('%Y%m%d')}.csv"
    fieldnames = ["Title", "Authors", "Published", "Link", "Abstract_EN", "Abstract_ZH", "One_Sentence_Summary", "Model_Type", "HHH_Focus", "Keywords"]

    with open(csv_file, "w", newline='', encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"\n✅ Saved {len(results)} relevant papers to {csv_file}")
