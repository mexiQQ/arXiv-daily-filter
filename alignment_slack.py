import requests
import pyfiglet
from datetime import datetime
import random

NOTION_LINK = "https://www.notion.so/arXiv-daily-alignment-papers-2086a18b889080978b3ec4312a41d300?source=copy_link"

def format_paper_message(paper: dict) -> str:
    """
    将论文信息格式化为 Slack markdown 消息
    """
    title = paper.get("Title", "").replace("\n", "").replace("\r", "").strip()
    authors = paper.get("Authors", "")
    model_type = paper.get("Model_Type", "Unknown")
    hhh_focus = paper.get("HHH_Focus", "N/A")
    keywords = paper.get("Keywords", "")
    published = paper.get("Published", "")
    abstract_en = paper.get("Abstract_EN", "")
    abstract_zh = paper.get("Abstract_ZH", "")
    one_sentence_summary = paper.get("One_Sentence_Summary", "")
    link = paper.get("Link", "#")

    message = (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*📌 New Paper on arXiv:*\n"
        f"*{title}*\n\n"
        # f"*Authors:* {authors}\n"
        f"*Model Type:* `{model_type}` | *HHH:* `{hhh_focus}` | *Published:* `{published}` \n"
        f"*Keywords:* {keywords}\n\n"
        f"*One Sentence Summary:* {one_sentence_summary}\n\n"
        # f"*Abstract_en:* {abstract_en}\n\n"
        # f"*Abstract_zh:* {abstract_zh}\n\n"
        f"*🔗 PDF Link:* <{link}|Click here>"
        "\n\n━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    return message

def send_slack_message(paper, webhook_url: str = "") -> None:
    """
    向 Slack 发送一条格式化文本消息
    """
    if not webhook_url:
        raise ValueError("Webhook URL must be provided")
    
    message = format_paper_message(paper)

    payload = {
        "text": message,
        "mrkdwn": True
    }
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"Slack send failed with status {response.status_code}: {response.text}"
        )

def send_slack_banner(webhook_url: str):
    today = datetime.now().strftime("%Y-%m-%d")

    # 使用 pyfiglet 生成 ASCII Art
    ascii_title = pyfiglet.figlet_format("arXiv Daily", font="big")
    ascii_block = f"```{ascii_title}```\n📅 *{today}*  \n📰 Papers related to alignment, safety, and LLMs below:\n"

    payload = {
        "text": ascii_block,
        "mrkdwn": True
    }

    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"Slack message failed: {response.status_code}, {response.text}"
        )


def format_paper_digest_summary(papers: list) -> str:
    """
    随机挑选 10 篇论文，生成简洁 Slack 消息摘要（用于 Digest 预览）
    """
    if len(papers) == 0:
        return "No papers available for summary."

    selected = random.sample(papers, min(len(papers), 5))

    header = (
        "*👋 Hello there!*\n"
        f"Here's your _arXiv Daily Filter {len(papers)} papers_ — a quick pick of today's papers related to *LLM alignment, safety, and helpfulness*.\n"
        f"👉 *[Full list in Notion]*: <{NOTION_LINK}|Click to view full database>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    body = ""
    for paper in selected:
        title = paper.get("Title", "").replace("\n", " ").strip()
        link = paper.get("Link", "#")
        keywords = paper.get("Keywords", "")
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        keyword_str = ", ".join(keyword_list[:3])  # 最多取 3 个

        body += f"📄 *<{link}|{title}>*\n"
        body += f"🧠 Keywords: {keyword_str}\n\n"

    footer = "━━━━━━━━━━━━━━━━━━━━━━"

    return header + body + footer

def send_slack_compressed_message(papers, webhook_url: str = "") -> None:
    """
    向 Slack 发送一条格式化文本消息
    """
    if not webhook_url:
        raise ValueError("Webhook URL must be provided")
    
    message = format_paper_digest_summary(papers)

    payload = {
        "text": message,
        "mrkdwn": True
    }
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"Slack send failed with status {response.status_code}: {response.text}"
        )
