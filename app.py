import json
import os
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# データ保存用のファイル名（前回と同じ）
DATA_FILE = 'events.json'

def load_events():
    """ファイルからイベントを読み込む"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_events(events):
    """ファイルにイベントを保存する"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

# --- ここから下が新しいデザイン（イメージ図を反映） ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LGBTQ+ Event Hub</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    
    <style>
        body {
            font-family: 'Noto Sans JP', sans-serif;
            background-color: #f5f5f5; /* 右側の薄グレー背景 */
            color: #333;
            margin: 0;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        /* --- ヘッダー（イメージ図の上部帯） --- */
        .navbar {
            background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%); /* ピンクのグラデーション */
            padding: 15px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
            color: #fff !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        .nav-link {
            color: #fff !important;
            font-weight: 400;
            margin-left: 15px;
        }
        .nav-link:hover {
            opacity: 0.8;
        }

        /* --- 全体のレイアウト（左ピンク、右グレー） --- */
        .main-container {
            display: flex;
            flex: 1;
        }

        /* --- 投稿フォームエリア（左側のピンク部分） --- */
        .form-section {
            width: 35%;
            background-color: #fff0f3; /* 薄いピンク背景 */
            padding: 40px;
            border-right: 1px solid #ffe0e6;
        }
        .form-section h3 {
            color: #ff6b81;
            font-weight: 700;
            margin-bottom: 30px;
            font-size: 1.3rem;
        }
        .form-label {
            font-weight: 700;
            color: #555;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        .form-control {
            border-radius: 8px;
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 15px;
            background-color: #fff;
        }
        .form-control:focus {
            border-color: #ff9a9e;
            box-shadow: 0 0 0 0.2rem rgba(255, 154, 158, 0.25);
        }
        .btn-submit {
            background: linear-gradient(135deg, #ff6b81 0%, #ff879c 100%);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 25px; /* 丸角ボタン */
            width: 100%;
            font-weight: 700;
            font-size: 1rem;
            margin-top: 10px;
            transition: 0.3s;
        }
        .btn-submit:hover {
            opacity: 0.9;
            transform: translateY(-2px);
        }

        /* --- イベント一覧エリア（右側のグレー部分） --- */
        .list-section {
            width: 65%;
            padding: 40px;
            background-color: #f5f5f5; /* 薄グレー背景 */
        }
        .list-section h3 {
            color: #555;
            font-weight: 700;
            margin-bottom: 30px;
            font-size: 1.3rem;
        }

        /* --- イベントカード（イメージ図の白い四角） --- */
        .event-card {
            background-color: #fff;
            border-radius: 15px; /* 丸角 */
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); /* 影 */
            display: flex;
            align-items: flex-start;
            transition: 0.3s;
            border: 1px solid #eee;
        }
        .event-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }

        /* --- 日付バッジ（パステルカラーの四角） --- */
        .date-badge {
            background-color: #ffe0e6; /* パステルピンク */
            color: #ff6b81;
            font-weight: 700;
            font-size: 0.9rem;
            padding: 8px 12px;
            border-radius: 8px;
            margin-right: 20px;
            text-align: center;
            min-width: 80px;
        }

        /* --- カード内のテキスト --- */
        .event-info {
            flex: 1;
        }
        .event-title {
            font-weight: 700;
            font-size: 1.2rem;
            margin-bottom: 5px;
            color: #333;
        }
        .event-place {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }
        .event-detail {
            color: #666;
            font-size: 0.95rem;
            line-height: 1.6;
            white-space: pre-wrap; /* 改行を反映 */
        }

        /* スマホ対応（画面が狭いときは縦並びに） */
        @media (max-width: 992px) {
            .main-container {
                flex-direction: column;
            }
            .form-section, .list-section {
                width: 100%;
                border-right: none;
                padding: 20px;
            }
        }
    </style>
</head>
<body>

    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">LGBTQ+ Event Hub</a>
            <div class="ms-auto d-flex">
                <a class="nav-link" href="#">ホーム</a>
                <a class="nav-link" href="#">イベント投稿</a>
                <a class="nav-link" href="#">マイページ</a>
                <a class="nav-link" href="#">ログイン</a>
            </div>
        </div>
    </nav>

    <div class="main-container">
        <div class="form-section">
            <h3>新しくイベントを投稿する</h3>
            <form method="POST" action="/post">
                <div class="mb-2">
                    <label class="form-label">開催日</label>
                    <input type="text" name="date" class="form-control" placeholder="6月1日 (土)" required>
                </div>
                <div class="mb-2">
                    <label class="form-label">イベント名</label>
                    <input type="text" name="title" class="form-control" placeholder="交流会、パレードなど" required>
                </div>
                <div class="mb-2">
                    <label class="form-label">場所</label>
                    <input type="text" name="place" class="form-control" placeholder="大阪・堂山町、オンラインなど" required>
                </div>
                <div class="mb-2">
                    <label class="form-label">主催者</label>
                    <input type="text" name="organizer" class="form-control" placeholder="団体名やニックネーム">
                </div>
                <div class="mb-2">
                    <label class="form-label">イベントの詳細</label>
                    <textarea name="detail" class="form-control" rows="5" placeholder="時間、参加費、持ち物など自由に書いてください"></textarea>
                </div>
                <button type="submit" class="btn btn-submit">イベントを公開する</button>
            </form>
        </div>

        <div class="list-section">
            <h3>📅 最新のイベント一覧</h3>
            
            {% if not events %}
                <div class="alert alert-light text-center border shadow-sm" style="border-radius: 15px;">
                    まだ投稿がありません。最初のイベントを投稿してみませんか？
                </div>
            {% endif %}

            {% for ev in events %}
                <div class="event-card">
                    <div class="date-badge">
                        {{ ev.date }}
                    </div>
                    <div class="event-info">
                        <div class="event-title">{{ ev.title }}</div>
                        <div class="event-place">
                            📍 {{ ev.place }}
                            {% if ev.organizer %}
                                <span class="ms-2">👤 主催: {{ ev.organizer }}</span>
                            {% endif %}
                        </div>
                        <div class="event-detail">{{ ev.detail }}</div>
                    </div>
                </div>
            {% endfor %}
        </div>
    </div>

</body>
</html>
"""

@app.route('/')
def index():
    events = load_events()
    return render_template_string(HTML_TEMPLATE, events=events)

@app.route('/post', methods=['POST'])
def post():
    events = load_events()
    # イメージ図に合わせて「organizer（主催者）」も保存するように追加
    new_event = {
        "title": request.form.get('title'),
        "date": request.form.get('date'),
        "place": request.form.get('place'),
        "organizer": request.form.get('organizer'),
        "detail": request.form.get('detail')
    }
    events.insert(0, new_event)
    save_events(events)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)