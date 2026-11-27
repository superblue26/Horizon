import os
import glob
import json
import asyncio
import datetime
from pathlib import Path
from email.utils import format_datetime
import urllib.request
from openai import OpenAI
import edge_tts

# 1. 自动寻找 ./docs 下最新生成的当天 Markdown 简报
docs_dir = Path("docs")
md_files = sorted(docs_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
target_md = next((f for f in md_files if f.name.lower() != "index.md" and "readme" not in f.name.lower()), None)

if not target_md:
    print("未找到当日生成的 Markdown 简报文件，跳过音频生成。")
    exit(0)

content = target_md.read_text(encoding="utf-8")
today_str = os.getenv("DATE") or datetime.date.today().strftime("%Y-%m-%d")

# 2. 调用 DeepSeek 将图文简报改写为 3~5 分钟自然口语播报稿
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

prompt = f"""你是一位专业、干练且有温度的双语晨间资讯主播。请将以下今日《Horizon 每日速递》Markdown 内容改写成一篇适合收听的播客口语稿（约 900-1300 中文字，语速适中约 4-5 分钟）。

要求：
1. 开场白简短亲切，报出今日日期（{today_str}）与核心看点。
2. 按板块清晰过渡，重点播报【建筑与设计】、【签证与移民】（美加澳新政策与机会），再精简串讲【科技】与【财经】要点。
3. 去掉所有 Markdown 符号、网址链接、评分数字和生硬列表，改为自然连贯的播音口语。
4. 在节目最后设置一个约 1 分钟的【今日雅思高频词】小环节，从文中挑出 3-4 个最具代表性的英文学术词汇，清晰念出英文单词、中文语境含义以及同义替换词（英文词汇与同义替换请直接保留英文拼写，方便语音引擎朗读英文发音）。
5. 结尾简短收尾即可。

今日简报原文：
{content[:14000]}
"""

print("正在生成播客口语稿...")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.4,
    max_tokens=2500
)
script_text = resp.choices[0].message.content.strip()

# 3. 使用 Edge-TTS 合成高质量中文+英文混读 MP3（云希/晓晓自然人声）
podcast_dir = docs_dir / "podcast"
podcast_dir.mkdir(parents=True, exist_ok=True)
mp3_filename = f"horizon-{today_str}.mp3"
mp3_path = podcast_dir / mp3_filename

async def synthesize():
    # zh-CN-YunxiNeural 或 zh-CN-XiaoxiaoNeural 均支持自然中英混读
    communicate = edge_tts.Communicate(script_text, voice="zh-CN-XiaoxiaoNeural", rate="+5%")
    await communicate.save(str(mp3_path))

print("正在合成 MP3 音频...")
asyncio.run(synthesize())

# 4. 自动生成/更新播客 RSS Feed (docs/podcast/podcast.xml)
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
      <title>Horizon 每日速递音频版 - {date_part}</title>
      <description>今日建筑与设计、美加澳新签证移民政策、科技财经及雅思词汇语音播报。</description>
      <pubDate>{pub_rfc822}</pubDate>
      <enclosure url="{item_url}" length="{size_bytes}" type="audio/mpeg" />
      <guid>{item_url}</guid>
    </item>""")

rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Horizon 每日速递 · 个人定制播客</title>
    <link>{base_url}/podcast.xml</link>
    <description>每日建筑设计、BIM远程机会、美加澳新工签移民动态与雅思学术词汇语音简报。</description>
    <language>zh-cn</language>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""
(podcast_dir / "podcast.xml").write_text(rss_xml, encoding="utf-8")
print(f"播客 RSS 已更新: {base_url}/podcast.xml")

# 5. 顺便向飞书发送一条带音频直链的收听通知
webhook_url = os.getenv("HORIZON_WEBHOOK_URL")
if webhook_url:
    payload = {
        "msg_type": "text",
        "content": {
            "text": f"🎧 Horizon 每日语音简报已生成 ({today_str})\n\n▶ 点击直接收听音频：\n{audio_url}\n\n📡 播客 App 订阅源（复制一次长期自动更新）：\n{base_url}/podcast.xml"
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
