import requests
import pyfiglet
from datetime import datetime
import random

NOTION_LINK = "https://www.notion.so/arXiv-daily-backdoor-papers-20a6a18b8890801c8ba7c734bccfba75?source=copy_link"

def format_paper_message(paper: dict) -> str:
    """
    将 Backdoor 相关论文格式化为 Slack 消息
    """
    title = paper.get("Title", "").replace("\n", "").replace("\r", "").strip()
    authors = paper.get("Authors", "")
    model_type = paper.get("Model_Type", "Unknown")
    use_intent = paper.get("Use_Intention", "Unknown")
    focus = paper.get("Focus", "Unknown")
    keywords = paper.get("Keywords", "")
    published = paper.get("Published", "")
    one_sentence_summary = paper.get("One_Sentence_Summary", "")
    link = paper.get("Link", "#")

    message = (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*📌 Backdoor-related Paper on arXiv:*\n"
        f"*{title}*\n\n"
        f"*Model Type:* `{model_type}` | *Use:* `{use_intent}` | *Focus:* `{focus}` | *Published:* `{published}` \n"
        f"*Keywords:* {keywords}\n\n"
        f"*📝 Summary:* {one_sentence_summary}\n\n"
        f"*🔗 PDF Link:* <{link}|Click here>\n"
        "\n━━━━━━━━━━━━━━━━━━━━━━"
    )
    return message


def send_slack_message(paper, webhook_url: str) -> None:
    """
    向 Slack 发送单条 Backdoor 论文消息
    """
    if not webhook_url:
        raise ValueError("Webhook URL is required.")
    
    message = format_paper_message(paper)
    payload = {"text": message, "mrkdwn": True}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Slack send failed: {response.status_code}, {response.text}")


def send_slack_banner(webhook_url: str):
    """
    发送 ASCII Banner 标题
    """
    today = datetime.now().strftime("%Y-%m-%d")
    ascii_title = pyfiglet.figlet_format("Backdoor Papers", font="big")
    ascii_block = f"```{ascii_title}```\n📅 *{today}*  \n🧪 Daily findings on backdoor research in LLMs/LMMs:\n"

    payload = {"text": ascii_block, "mrkdwn": True}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Slack banner failed: {response.status_code}, {response.text}")


def format_paper_digest_summary(papers: list) -> str:
    """
    随机挑选 10 篇 Backdoor 相关论文，生成摘要消息
    """
    if len(papers) == 0:
        return "No backdoor-related papers found today."

    selected = random.sample(papers, min(len(papers), 10))

    header = (
        "*🛡️ Backdoor Digest Summary*\n"
        f"Today's backdoor-related papers ({len(papers)} total): curated from arXiv\n"
        f"👉 *[Full Notion List]*: <{NOTION_LINK}|Click here>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    body = ""
    for paper in selected:
        title = paper.get("Title", "").replace("\n", " ").strip()
        link = paper.get("Link", "#")
        keywords = paper.get("Keywords", "")
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        keyword_str = ", ".join(keyword_list[:3])  # Top 3

        body += f"📄 *<{link}|{title}>*\n"
        body += f"🧠 Keywords: {keyword_str}\n\n"

    footer = "━━━━━━━━━━━━━━━━━━━━━━"
    return header + body + footer


def send_slack_compressed_message(papers: list, webhook_url: str):
    """
    发送 Backdoor Digest 摘要消息
    """
    if not webhook_url:
        raise ValueError("Webhook URL is required.")

    message = format_paper_digest_summary(papers)
    payload = {"text": message, "mrkdwn": True}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Slack send failed: {response.status_code}, {response.text}")

