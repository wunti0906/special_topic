from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
import os
import json

# 設定 template 資料夾位置（Vercel 結構需求）
# 如果你的 HTML 在專案根目錄的 templates 資料夾，請保持這個設定
app = Flask(__name__, template_folder='../templates')

# Google Sheets 權限範圍
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gsheet():
    # 從 Vercel 環境變數讀取名為 'G_JSON' 的設定
    g_json_str = os.environ.get('G_JSON')
    if not g_json_str:
        raise ValueError("找不到環境變數 G_JSON，請在 Vercel Settings 中設定。")
    
    # 解析 JSON 字串
    try:
        service_account_info = json.loads(g_json_str)
    except json.JSONDecodeError:
        raise ValueError("環境變數 G_JSON 格式錯誤，請確認是否包含完整的大括號 { }")

    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
    client = gspread.authorize(creds)
    
    # 請確保你的 Google 試算表名稱「完全等於」這四個字
    try:
        return client.open("問卷回覆").get_worksheet(0)
    except Exception:
        raise FileNotFoundError("找不到名為『問卷回覆』的試算表，或機器人 Email 未加入共用編輯者。")

@app.route('/')
def index():
    return render_template('survey.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # 1. 獲取表單數據
        raw_data = request.form.to_dict(flat=False)
        
        # 2. 處理資料格式：將多選題 list 轉為字串
        row_data = ["; ".join(value) for value in raw_data.values()]
        
        # ⚠️ 重點：這裡絕對不能有 open('survey_results.csv'...) 相關的程式碼
        
        # 3. 僅將資料寫入 Google Sheets
        sheet = get_gsheet()
        sheet.append_row(row_data)
        
        return """
        <div style="text-align:center; padding-top:50px; font-family:sans-serif;">
            <h1 style="color:#2ecc71;">提交成功！</h1>
            <p>您的回覆已安全存入 Google 雲端試算表。</p>
            <a href="/" style="color:#3498db; text-decoration:none;">返回填寫下一份</a>
        </div>
        """
    except Exception as e:
        # 發生錯誤時回傳錯誤訊息，方便除錯
        return f"<div style='color:red; padding:20px;'><h3>發生錯誤</h3><p>{str(e)}</p></div>"
# Vercel 部署必須
app.debug = True

if __name__ == '__main__':
    app.run(debug=True, port=5000)