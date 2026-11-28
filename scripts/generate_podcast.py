import os
import re
import json
import shutil
import asyncio
import datetime
from pathlib import Path
from email.utils import format_datetime
import urllib.request
from openai import OpenAI
import edge_tts


def clean_for_tts(text: str) -> str:
    """彻底清除所有半角/全角 Markdown 符号、装饰符与链接，杜绝 TTS 念出'星号''井号'"""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*#`~>|_•·＊＃＿～｜・●◆■★☆※▶►]+", " ", text)
    text = re.sub(r"^\s*[-—–]+\s*", "", text, flags=re.MULTILINE)
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

# 2. 调用 DeepSeek 生成纯文本播报稿（强制包含完整英文新闻段落朗读 + 5个雅思词汇）
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

prompt = f"""你是一位专业、干练且中英文发音俱佳的双语晨间资讯主播。请根据以下今日《Horizon 每日速递》内容，撰写一篇适合直接语音朗读的纯文本播客稿（约 1400-1800 字，时长约 6 分钟）。

【格式铁律 - 违反任何一条都会导致语音播报出错】：
1. 全文必须是纯粹的口语化段落，绝对禁止出现任何星号、井号、短横线、下划线、括号标签或项目符号！不要加任何标题符号。
2. 段落之间用空行分隔，用于控制语音停顿。

【节目内容与结构（必须严格按以下顺序完整输出）】：

第一部分：今日核心资讯串讲（约 3 分钟）
用自然流畅的播音员口吻，先报出今日日期（{today_str}），然后依次串讲建筑与设计、签证与移民（重点提美加澳新政策与机会）、科技新闻、财经新闻的核心看点。直接用连贯句子讲述，不要列清单。

第二部分：英文新闻原文精读（约 1.5 分钟）
选取今天简报中最有价值的一条财经、移民政策或建筑行业新闻，用专业英文财经/建筑媒体（如 Financial Times 或 Architectural Record）的报道风格，撰写一段完整、地道的英文新闻原文段落（严格控制在 90 到 120 个英文单词之间，包含背景、具体数据或政策细节、行业影响）。
播报方式：先用一句中文引入（例如：“接下来进入今天的英文原文精读环节，我们聚焦……请听英文原文。”），然后完整、连贯地输出这段英文原文段落。注意：英文段落内部绝对不要夹杂任何中文翻译！

第三部分：原文核心意思与 5 个雅思高频词汇精讲（约 1.5 分钟）
英文原文结束后，先用两句中文概括这段英文的核心大意。
然后从刚才那段英文原文中，挑出 5 个最具代表性的雅思阅读或听力高频学术词汇进行讲解。每个词严格按照以下纯口语模板展开：
“第一个词，英文单词，中文意思是某某，在雅思考试中常见的同义替换有：英文词一，英文词二。”
（以此类推讲完 5 个词，最后用一句话自然收尾结束节目。）

今日简报素材：
{content[:15000]}
"""

print("正在生成新版播客口语稿...")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.4,
    max_tokens=3200
)
raw_script = resp.choices[0].message.content.strip()
script_text = clean_for_tts(raw_script)

print("=== 清洗后送入 TTS 的文稿预览（前 600 字） ===")
print(script_text[:600])
print("==============================================")

# 3. 使用 Edge-TTS 合成高质量中英混读 MP3，并同步封面图到 docs/podcast/
podcast_dir = docs_dir / "podcast"
podcast_dir.mkdir(parents=True, exist_ok=True)
mp3_filename = f"horizon-{today_str}.mp3"
mp3_path = podcast_dir / mp3_filename

root_cover = Path("cover.jpg")
podcast_cover = podcast_dir / "cover.jpg"
if root_cover.exists():
    shutil.copy2(root_cover, podcast_cover)
    print(f"✅ 已同步播客封面至 {podcast_cover}")
else:
    print("⚠️ 未在仓库根目录找到 cover.jpg，RSS 仍将引用封面 URL")


async def synthesize():
    communicate = edge_tts.Communicate(script_text, voice="zh-CN-XiaoxiaoNeural", rate="+2%")
    await communicate.save(str(mp3_path))


print("正在合成 MP3 音频...")
asyncio.run(synthesize())

# 4. 更新播客 RSS Feed (docs/podcast/podcast.xml)
repo_owner, repo_name = os.getenv("GITHUB_REPOSITORY", "superblue26/Horizon").split("/")
base_url = f"https://{repo_owner.lower()}.github.io/{repo_name}/podcast"
audio_url = f"{base_url}/{mp3_filename}"
cover_url = f"{base_url}/cover.jpg"

mp3_files = sorted(podcast_dir.glob("horizon-*.mp3"), reverse=True)[:30]
items_xml = []
for f in mp3_files:
    date_part = f.stem.replace("horizon-", "")
    size_bytes = f.stat().st_size
    pub_dt = datetime.datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    pub_rfc822 = format_datetime(pub_dt)
    item_url = f"{base_url}/{f.name}"
    items_xml.append(
        f"""    <item>
      <title>Horizon 每日速递与英文精读 - {date_part}</title>
      <description>今日建筑与设计、美加澳新签证移民政策、科技财经资讯及英文原文精读与雅思词汇。</description>
      <pubDate>{pub_rfc822}</pubDate>
      <enclosure url="{item_url}" length="{size_bytes}" type="audio/mpeg" />
      <guid>{item_url}</guid>
    </item>"""
    )

items_block = "\n".join(items_xml)
rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Horizon 每日速递 · 个人定制播客</title>
    <link>{base_url}/podcast.xml</link>
    <description>每日建筑设计、BIM远程机会、美加澳新工签移民动态，附英文原声精读与雅思学术词汇。</description>
    <language>zh-cn</language>
    <itunes:author>Horizon AI</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="{cover_url}" />
    <image>
      <url>{cover_url}</url>
      <title>Horizon 每日速递 · 个人定制播客</title>
      <link>{base_url}/podcast.xml</link>
    </image>
{items_block}
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
            "text": f"🎧 Horizon 每日语音简报已更新 ({today_str})\n（含英文新闻原文精读 + 5个雅思高频词汇）\n\n▶ 点击直接收听音频：\n{audio_url}"
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
