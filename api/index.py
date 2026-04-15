from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
import os
import json

# Vercel 結構：HTML 通常在 templates 資料夾
app = Flask(__name__, template_folder='../templates')

SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def get_gsheet():
    # 讀取環境變數
    g_json_str = os.environ.get('G_JSON')
    if not g_json_str:
        raise ValueError("錯誤：找不到環境變數 G_JSON。請在 Vercel Settings 設定。")
    
    try:
        service_account_info = json.loads(g_json_str)
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
        client = gspread.authorize(creds)
        
        # 開啟試算表
        return client.open("問卷回覆").get_worksheet(0)
    except json.JSONDecodeError:
        raise ValueError("錯誤：G_JSON 格式不正確，請確認是否包含完整大括號 { }。")
    except gspread.exceptions.SpreadsheetNotFound:
        raise FileNotFoundError("錯誤：找不到名為『問卷回覆』的試算表，請確認檔名完全一致。")
    except Exception as e:
        raise Exception(f"連線 Google 發生其他錯誤：{str(e)}")

@app.route('/')
def index():
    return render_template('survey.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # 獲取表單數據
        raw_data = request.form.to_dict(flat=False)
        # 處理資料格式：將 list 轉為字串
        row_data = ["; ".join(value) for value in raw_data.values()]
        
        # 寫入 Google Sheets (已移除任何 CSV 寫入邏輯)
        sheet = get_gsheet()
        sheet.append_row(row_data)
        
        return """
        <div style="text-align:center; padding-top:50px; font-family:sans-serif;">
            <h1 style="color:#2ecc71;">提交成功！</h1>
            <p>您的回覆已存入 Google 試算表。</p>
            <a href="/" style="color:#3498db; text-decoration:none;">返回填寫下一份</a>
        </div>
        """
    except Exception as e:
        # 將具體錯誤顯示在網頁上，不用再去翻 Logs
        return f"""
        <div style='color:red; padding:20px; font-family:sans-serif; border:2px solid red;'>
            <h3>提交失敗</h3>
            <p><strong>具體原因：</strong> {str(e)}</p>
            <hr>
            <p>如果是 OSError Read-only，代表 Vercel 沒抓到新版代碼，請執行 Redeploy 並清除快取。</p>
        </div>
        """

if __name__ == '__main__':
    app.run(debug=True, port=5000)