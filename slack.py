import requests
from env import SLACK_WEBHOOK_URL, SLACK_WEBHOOK_URL_MY

def format_paper_message(paper: dict, webhook_url=SLACK_WEBHOOK_URL) -> str:
    """
    将论文信息格式化为 Slack markdown 消息
    """
    title = paper.get("Title", "")
    authors = paper.get("Authors", "")
    model_type = paper.get("Model_Type", "Unknown")
    hhh_focus = paper.get("HHH_Focus", "N/A")
    keywords = paper.get("Keywords", "")
    published = paper.get("Published", "")
    abstract_en = paper.get("Abstract_EN", "")
    abstract_zh = paper.get("Abstract_ZH", "")
    one_sentence_summary = paper.get("One_Sentence_Summary", "")
    link = paper.get("Link", "#")

    if webhook_url == SLACK_WEBHOOK_URL_MY:
        message = (
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*📌 New Paper on arXiv:*\n"
            f"*{title}*\n\n"
            f"*Authors:* {authors}\n"
            f"*Published:* {published}\n"
            f"*Model Type:* `{model_type}` | *HHH:* `{hhh_focus}`\n"
            f"*Keywords:* {keywords}\n\n"
            f"*One Sentence Summary:* {one_sentence_summary}\n\n"
            f"*Abstract_en:* {abstract_en}\n\n"
            f"*Abstract_zh:* {abstract_zh}\n\n"
            f"*🔗 PDF Link:* <{link}|Click here>"
            "\n\n━━━━━━━━━━━━━━━━━━━━━━"
        )
    elif webhook_url == SLACK_WEBHOOK_URL:
        message = (
            f"*📌 New Paper on arXiv:*\n"
            f"*{title}*\n\n"
            f"*Authors:* {authors}\n"
            f"*Published:* {published}\n"
            f"*Model Type:* `{model_type}` | *HHH:* `{hhh_focus}`\n"
            f"*Keywords:* {keywords}\n\n"
            f"*One Sentence Summary:* {one_sentence_summary}\n\n"
            f"*Abstract_en:* {abstract_en}\n\n"
            f"*🔗 PDF Link:* <{link}|Click here>"
        ) 
    return message

def send_slack_message(paper, webhook_url: str = SLACK_WEBHOOK_URL) -> None:
    """
    向 Slack 发送一条格式化文本消息
    """
    message = format_paper_message(paper, webhook_url)

    payload = {
        "text": message,
        "mrkdwn": True
    }
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(
            f"Slack send failed with status {response.status_code}: {response.text}"
        )

