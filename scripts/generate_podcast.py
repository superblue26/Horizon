import os
import re
import json
import asyncio
import datetime
from pathlib import Path
from email.utils import format_datetime
import urllib.request
from openai import OpenAI
import edge_tts


def clean_for_tts(text: str) -> str:
    """彻底清除 Markdown 符号、URL 和特殊标点，防止 TTS 念出'星号'等干扰词"""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # 保留链接文字，去掉 URL
    text = re.sub(r"https?://\S+", "", text)               # 清除裸链接
    text = re.sub(r"[*#_`~>|]+", " ", text)                # 彻底删除星号、井号、下划线等符号
    text = re.sub(r"^\s*[-•·]\s*", "", text, flags=re.MULTILINE)  # 去掉行首项目符号
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# 1. 自动寻找 ./docs 下最新生成的当天 Markdown 简报
docs_dir = Path("docs")
md_files = sorted(docs_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
target_md = next((f for f in md_files if f.name.lower() != "index.md" and "readme" not in f.name.lower()), None)

if not target_md:
    print("未找到当日生成的 Markdown 简报文件，跳过音频生成。")
    exit(0)

content = target_md.read_text(encoding="utf-8")
today_str = os.getenv("DATE") or datetime.date.today().strftime("%Y-%m-%d")

# 2. 调用 DeepSeek 生成纯口语播报稿（含英文原文段落精读 + 4~6个雅思词汇）
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

prompt = f"""你是一位专业、干练且中英文发音俱佳的双语晨间资讯主播。请根据以下今日《Horizon 每日速递》内容，撰写一篇适合直接语音朗读的播客纯文本口语稿（总字数约 1200-1600 字，时长约 5-6 分钟）。

【严格格式要求 - 极其重要】：
- 全文必须是纯粹的自然口语段落，绝对禁止出现任何 Markdown 符号（严禁出现星号 *、井号 #、短横线 -、下划线 _、方括号 []、网址链接或评分数字），因为语音引擎会把符号直接念出来！
- 段落之间用空行分隔，以便语音播报自然停顿。

【节目结构要求】：
第一部分：今日核心资讯串讲（约 3 分钟）
1. 简短亲切的开场白，报出今日日期（{today_str}）。
2. 按板块自然过渡，重点播报【建筑与设计】、【签证与移民】（美加澳新政策与机会），再精简串讲【科技】与【财经】核心动态。

第二部分：今日英文原声精读与雅思词汇（约 2-3 分钟）
1. 从今天涉及建筑设计、社会政策或财经金融的英文新闻中，挑选或提炼一段最具代表性的地道英文新闻原文段落（约 80 到 120 个英文单词，逻辑完整、有学术和职场含金量）。
2. 先用中文自然引入，然后完整、流畅地朗读这段英文原文（不要在英文句子中间插中文翻译，保持原声听力沉浸感）。
3. 原文朗读结束后，先用 1-2 句中文概括这段英文的核心意思。
4. 接着挑出这段原文中出现的 4 到 6 个雅思高频学术词汇进行精讲。每个词请按这样的自然口语节奏讲解：“第X个词，英文单词，中文意思是某某，在雅思考试中常见的同义替换有：英文同义词一，英文同义词二。”
5. 简短自然地结束今日节目。

今日简报原文：
{content[:15000]}
"""

print("正在生成新版播客口语稿...")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.4,
    max_tokens=3000
)
raw_script = resp.choices[0].message.content.strip()
script_text = clean_for_tts(raw_script)

# 3. 使用 Edge-TTS 合成高质量中英混读 MP3
podcast_dir = docs_dir / "podcast"
podcast_dir.mkdir(parents=True, exist_ok=True)
mp3_filename = f"horizon-{today_str}.mp3"
mp3_path = podcast_dir / mp3_filename


async def synthesize():
    communicate = edge_tts.Communicate(script_text, voice="zh-CN-XiaoxiaoNeural", rate="+3%")
    await communicate.save(str(mp3_path))


print("正在合成 MP3 音频...")
asyncio.run(synthesize())

# 4. 自动生成/更新兼容 Apple Podcasts 的播客 RSS Feed (docs/podcast/podcast.xml)
repo_owner, repo_name = os.getenv("GITHUB_REPOSITORY", "superblue26/Horizon").split("/")
base_url = f"https://{repo_owner.lower()}.github.io/{repo_name}/podcast"
audio_url = f"{base_url}/{mp3_filename}"

mp3_files = sorted(podcast_dir.glob("horizon-*.mp3"), reverse=True)[:30]
items_xml = []
for f in mp3_files:
    date_part = f.stem.replace("horizon-", "")
    size_bytes = f.stat().st_size
    pub_dt = datetime.datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    pub_rfc822 = format_datetime(pub_dt)
    item_url = f"{base_url}/{f.name}"
    items_xml.append(f"""    <item>
      <title>Horizon 每日速递与英文精读 - {date_part}</title>
      <description>今日建筑与设计、美加澳新签证移民政策、科技财经资讯及英文原文精读与雅思词汇。</description>
      <pubDate>{pub_rfc822}</pubDate>
      <enclosure url="{item_url}" length="{size_bytes}" type="audio/mpeg" />
      <guid>{item_url}</guid>
    </item>""")

rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Horizon 每日速递 · 个人定制播客</title>
    <link>{base_url}/podcast.xml</link>
    <description>每日建筑设计、BIM远程机会、美加澳新工签移民动态，附英文原声精读与雅思学术词汇。</description>
    <language>zh-cn</language>
    <itunes:author>Horizon AI</itunes:author>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""
(podcast_dir / "podcast.xml").write_text(rss_xml, encoding="utf-8")
print(f"播客 RSS 已更新: {base_url}/podcast.xml")

# 5. 向飞书发送音频直链通知
webhook_url = os.getenv("HORIZON_WEBHOOK_URL")
if webhook_url:
    payload = {
        "msg_type": "text",
        "content": {
            "text": f"🎧 Horizon 每日语音简报已更新 ({today_str})\n（含英文原声段落精读 + 4-6个雅思高频词汇）\n\n▶ 点击直接收听音频：\n{audio_url}"
        }
    }
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print("飞书语音通知发送成功！")
    except Exception as e:
        print(f"飞书通知发送失败: {e}")
