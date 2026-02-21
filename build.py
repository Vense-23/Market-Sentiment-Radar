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
            for entry in f.entries[:50]: 
                content += f"[{name}] {entry.title}\n"
        except Exception as e:
            print(f"抓取 {name} 失败: {e}")
    return content

def get_ai_analysis(raw_text):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.now(tz).strftime("%Y年%m月%d日")
    
    prompt = f"""
    你现在是一个服务于一线实战派参与者的顶级美股情绪分析引擎。
    请基于今日（{today_str}）Reddit 最新数据（近200条讨论），生成极度硬核的中文网页简报。
    
    分析核心要求（必须严格遵守）：
    1. 【严格的杂音过滤（Negative Prompt）】：
       - 绝对禁止收录券商软件故障、账户无法交易、期权限制、出入金问题（如 Moomoo/FUTU, JPM, Robinhood, BAC 等客服类话题）。
       - 绝对禁止将 SPY, QQQ 等大盘 ETF 列为个股。
    
    2. 【指定版块一：热议中的个股和想法】：
       - 请输出一个明确的二级标题：<h2>热议中的个股和想法</h2>
       - 筛选标准：仅限今日有高频提及、包含基本面或交易情绪博弈的上市公司（宁缺毋滥，10-20只）。按顺序“1. 2. 3...”垂直向下排列。
       - 【非常重要：评论归位】：在每只个股下方，**必须**把原帖中关于该股的高质量、理性的评论（例如对该公司的长线定位、业务分析等）直接摘录在这里！不要把针对具体公司的优质评论漏掉或扔在后面的产业链板块里。个股下面必须有丰满的引用支撑！
       - 摘录格式：必须包含英文原文和中文翻译。

    3. 【指定版块二：AI 产业链深度追踪】：
       - 请输出一个明确的二级标题：<h2>AI 产业链深度追踪</h2>
       - 聚焦：模型、算、光、存、电、板、云。
       - 这里的摘录主要用于展示针对整个行业、技术趋势、供应链博弈等“宏大叙事”的讨论（5-10条），具体公司的讨论优先放在上面的个股板块中。

    4. 【排版要求】：只输出内部的 HTML 元素。<blockquote class="quote"> 用于包裹原文摘录。如果有连续的多条摘录，请将它们分多个 blockquote 堆叠排列。原文要求原汁原味，并附带中文翻译。

    今日原始讨论数据池：
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
                --text-main: #f1f5f9;
                --text-muted: #94a3b8;
                --accent: #38bdf8;
                --border: #334155;
            }}
            body {{ background: var(--bg); color: var(--text-main); font-family: -apple-system, sans-serif; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 900px; margin: auto; }}
            h1 {{ color: var(--accent); border-bottom: 2px solid var(--border); padding-bottom: 10px; font-size: 1.8rem; }}
            h2 {{ color: #fbbf24; margin-top: 40px; border-bottom: 1px solid #334155; padding-bottom: 8px; font-size: 1.5rem; }}
            h3 {{ color: #38bdf8; margin-top: 20px; font-size: 1.2rem; }}
            .time {{ color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px; }}
            
            ol {{ padding-left: 20px; margin-top: 20px; }}
            ol li {{ margin-bottom: 40px; font-size: 1.1rem; border-bottom: 1px dashed var(--border); padding-bottom: 20px; }}
            ol li strong {{ color: var(--accent); font-size: 1.3rem; }}
            
            blockquote, .quote {{
                background: #020617;
                border-left: 4px solid #10b981;
                padding: 12px 15px;
                margin: 12px 0;
                color: #cbd5e1;
                font-size: 0.95rem;
                font-style: normal;
                border-radius: 4px;
                line-height: 1.6;
            }}
            .translation {{ color: #94a3b8; margin-top: 8px; font-size: 0.9rem; border-top: 1px dotted #334155; padding-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 {today_str} 市场异动个股与AI产业链透视</h1>
            <p class="time">情报源头: 200+ 最新高热原帖 | 最后分析时间: {update_time} (北京时间)</p>
            {report}
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    print("开始大批量抓取今日 200+ 原始数据...")
    data = fetch_data()
    print("Gemini 正在执行严苛过滤与深度海量摘录...")
    analysis = get_ai_analysis(data)
    print("生成网页...")
    generate_html(analysis)
