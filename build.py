import feedparser
import os
import google.generativeai as genai
from datetime import datetime
import pytz

# 1. 抓取 Reddit 全美股热门板块
def fetch_data():
    feeds = {
        "WSB(高热情绪)": "https://www.reddit.com/r/wallstreetbets/.rss",
        "Stocks(主流讨论)": "https://www.reddit.com/r/stocks/.rss"
    }
    content = ""
    for name, url in feeds.items():
        try:
            # 使用 User-Agent 伪装，确保在 GitHub 环境下也能顺利抓取
            f = feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            for entry in f.entries[:12]:
                content += f"[{name}] {entry.title}\n"
        except Exception as e:
            print(f"抓取 {name} 失败: {e}")
    return content

# 2. 调用 Gemini 进行专业化总结
def get_ai_analysis(raw_text):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    你现在是一个资深美股分析助手。请分析以下 Reddit 热议标题并生成中文网页简报。
    
    分析维度：
    1. 【全市场扫描】：找出当前热度最高的 3-5 只美股个股（不论行业）。
    2. 【科技股透视】：重点分析 AI 芯片、光模块、互联网巨头（特别是 Google 动态）、软件应用的讨论异动。
    3. 【风险/机会】：总结散户目前的共识或极度分歧点。
    
    请直接输出 HTML 元素内容（不要包含 markdown 标签），内容要专业、精准。
    原始数据：
    {raw_text}
    """
    response = model.generate_content(prompt)
    return response.text.replace("```html", "").replace("```", "").strip()

# 3. 生成专业深色模式网页
def generate_html(report):
    tz = pytz.timezone('Asia/Shanghai')
    update_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>实战派 | 美股情绪雷达</title>
        <style>
            body {{ background: #0f172a; color: #e2e8f0; font-family: sans-serif; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; background: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #334155; }}
            h1 {{ color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
            .time {{ color: #94a3b8; font-size: 0.8rem; margin-bottom: 20px; }}
            li {{ margin-bottom: 12px; }}
            strong {{ color: #fbbf24; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔭 美股散户情绪雷达</h1>
            <p class="time">最后更新: {update_time} (北京时间)</p>
            <div>{report}</div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    data = fetch_data()
    analysis = get_ai_analysis(data)
    generate_html(analysis)
