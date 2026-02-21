import feedparser
import os
import google.generativeai as genai
from datetime import datetime
import pytz

def fetch_data():
    feeds = {
        "WSB(散户情绪)": "https://www.reddit.com/r/wallstreetbets/.rss",
        "Stocks(主流个股)": "https://www.reddit.com/r/stocks/.rss",
        "Options(期权异动)": "https://www.reddit.com/r/options/.rss",
        "Investing(长线逻辑)": "https://www.reddit.com/r/investing/.rss"
    }
    content = ""
    for name, url in feeds.items():
        try:
            f = feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            for entry in f.entries[:20]: # 增加单版块抓取量，确保样本充足
                content += f"[{name}] {entry.title}\n"
        except Exception as e:
            print(f"抓取 {name} 失败: {e}")
    return content

def get_ai_analysis(raw_text):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 动态注入今天的日期
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.now(tz).strftime("%Y年%m月%d日")
    
    prompt = f"""
    你现在是一个顶级美股量化与基本面分析助手。
    请基于今日（{today_str}）Reddit 核心讨论区的最新数据，生成深度中文网页简报。
    
    分析核心要求（必须严格遵守）：
    1. 【筛选标准说明】：在简报最开头，简短说明你的高热度筛选标准（必须明确提及是基于 {today_str} 当日新增帖子的“提及频次、情绪分歧度以及产业链边际变化”）。
    2. 【严格限制的 TOP 20 个股】：
       - 只能列出**具体的上市公司个股**（Ticker）。**绝对禁止**列出 SPY、QQQ 等 ETF，**绝对禁止**列出宏观话题或泛行业名称。
       - 必须采用纯垂直排版，按顺序“1. 2. 3...”向下排列，严禁使用并排的小框框或网格排版。
       - 在每个个股的分析逻辑下方，直接摘录 1-2 句当日该股票相关的核心高质量原文讨论（可用中文翻译呈现，使用带有引用的样式）。
    3. 【AI 产业链深度追踪】：
       - 聚焦：模型、算、光（含中际旭创相关的上游）、存、电（组件、发电、电网）、板、云（如 Google 等动态）。
       - 必须在相关产业链板块下方，汇总摘录 5-10 个当日新增的、写得最精彩的 Reddit 原文观点（明确标注出处和讨论方向）。
    4. 【排版要求】：只输出内部的 HTML 元素，使用原生的 <ol> 或 <ul> 列表，以及 <blockquote class="quote"> 来包裹原文摘录，不要加内联样式破坏深色主题。

    今日原始讨论数据：
    {raw_text}
    """
    response = model.generate_content(prompt)
    return response.text.replace("```html", "").replace("```", "").strip()

def generate_html(report):
    tz = pytz.timezone('Asia/Shanghai')
    update_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    today_str = datetime.now(tz).strftime("%m月%d日")
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{today_str} 核心个股与AI雷达</title>
        <style>
            :root {{
                --bg: #0f172a;
                --card-bg: #1e293b;
                --text-main: #f1f5f9;
                --text-muted: #94a3b8;
                --accent: #38bdf8;
                --border: #334155;
            }}
            body {{ background: var(--bg); color: var(--text-main); font-family: -apple-system, sans-serif; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 900px; margin: auto; }}
            h1 {{ color: var(--accent); border-bottom: 2px solid var(--border); padding-bottom: 10px; font-size: 1.8rem; }}
            h2, h3 {{ color: #fbbf24; margin-top: 30px; }}
            .time {{ color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px; }}
            .intro-box {{ background: rgba(56, 189, 248, 0.1); border-left: 4px solid var(--accent); padding: 15px; margin-bottom: 30px; border-radius: 0 8px 8px 0; }}
            
            /* 强制列表垂直排列，消除网格卡片 */
            ol {{ padding-left: 20px; margin-top: 20px; }}
            ol li {{ margin-bottom: 25px; font-size: 1.1rem; border-bottom: 1px dashed var(--border); padding-bottom: 15px; }}
            ol li strong {{ color: var(--accent); font-size: 1.2rem; }}
            
            /* 原文摘录的专属样式 */
            blockquote, .quote {{
                background: #020617;
                border-left: 4px solid #10b981; /* 绿色引用条，更显眼 */
                padding: 12px 15px;
                margin: 10px 0;
                color: #cbd5e1;
                font-size: 0.95rem;
                font-style: italic;
                border-radius: 4px;
            }}
            .quote-label {{ font-size: 0.8rem; color: #10b981; font-weight: bold; font-style: normal; display: block; margin-bottom: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 {today_str} 美股极热个股与AI产业链透视</h1>
            <p class="time">系统抓取时间: {update_time} (北京时间)</p>
            {report}
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    print("开始精准抓取今日数据...")
    data = fetch_data()
    print("Gemini 正在执行严格过滤与摘录...")
    analysis = get_ai_analysis(data)
    print("重新渲染深色沉浸式排版...")
    generate_html(analysis)
