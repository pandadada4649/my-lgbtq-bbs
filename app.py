import json
import os
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

DATA_FILE = 'events.json'

def load_events():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_events(events):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

# デザインと絞り込み機能を含めたテンプレート
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
        body { font-family: 'Noto Sans JP', sans-serif; background-color: #f5f5f5; color: #333; margin: 0; min-height: 100vh; }
        
        .navbar { background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%); padding: 15px 20px; }
        .navbar-brand { font-weight: 700; font-size: 1.5rem; color: #fff !important; }

        .main-container { display: flex; }

        /* 左側：フォーム */
        .form-section { width: 35%; background-color: #fff0f3; padding: 40px; border-right: 1px solid #ffe0e6; }
        .form-section h3 { color: #ff6b81; font-weight: 700; margin-bottom: 25px; font-size: 1.2rem; }
        
        /* 右側：一覧 */
        .list-section { width: 65%; padding: 40px; }

        /* 絞り込みボタン（右上イメージ） */
        .filter-container { margin-bottom: 30px; display: flex; gap: 10px; flex-wrap: wrap; }
        .btn-filter { 
            border-radius: 20px; border: 2px solid #ff9a9e; background: white; color: #ff6b81;
            padding: 5px 20px; font-weight: 700; transition: 0.3s; text-decoration: none; font-size: 0.9rem;
        }
        .btn-filter:hover, .btn-filter.active { background: #ff9a9e; color: white; }

        /* イベントカード */
        .event-card { 
            background: #fff; border-radius: 15px; padding: 20px; margin-bottom: 20px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); display: flex; border: 1px solid #eee;
        }
        .genre-tag {
            font-size: 0.75rem; padding: 2px 10px; border-radius: 10px; background: #eee; color: #666; margin-bottom: 10px; display: inline-block;
        }
        .date-badge { background-color: #ffe0e6; color: #ff6b81; font-weight: 700; padding: 8px 12px; border-radius: 8px; margin-right: 20px; min-width: 80px; text-align: center; }
        
        .btn-submit { background: linear-gradient(135deg, #ff6b81 0%, #ff879c 100%); color: white; border: none; padding: 12px; border-radius: 25px; width: 100%; font-weight: 700; margin-top: 10px; }

        @media (max-width: 992px) { .main-container { flex-direction: column; } .form-section, .list-section { width: 100%; } }
    </style>
</head>
<body>

    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">LGBTQ+ Event Hub</a>
        </div>
    </nav>

    <div class="main-container">
        <div class="form-section">
            <h3>新しくイベントを投稿する</h3>
            <form method="POST" action="/post">
                <div class="mb-3">
                    <label class="form-label">ジャンル</label>
                    <select name="genre" class="form-select" required>
                        <option value="ゲイ">ゲイ</option>
                        <option value="レズ">レズ</option>
                        <option value="トランス">トランス</option>
                        <option value="その他">その他</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">開催日</label>
                    <input type="text" name="date" class="form-control" placeholder="6月1日 (土)" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">イベント名</label>
                    <input type="text" name="title" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">場所</label>
                    <input type="text" name="place" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">詳細</label>
                    <textarea name="detail" class="form-control" rows="4"></textarea>
                </div>
                <button type="submit" class="btn btn-submit">公開する</button>
            </form>
        </div>

        <div class="list-section">
            <div class="filter-container">
                <a href="/" class="btn-filter {% if current_genre == 'all' %}active{% endif %}">すべて</a>
                <a href="/?genre=ゲイ" class="btn-filter {% if current_genre == 'ゲイ' %}active{% endif %}">ゲイ</a>
                <a href="/?genre=レズ" class="btn-filter {% if current_genre == 'レズ' %}active{% endif %}">レズ</a>
                <a href="/?genre=トランス" class="btn-filter {% if current_genre == 'トランス' %}active{% endif %}">トランス</a>
                <a href="/?genre=その他" class="btn-filter {% if current_genre == 'その他' %}active{% endif %}">その他</a>
            </div>

            {% for ev in events %}
                <div class="event-card">
                    <div class="date-badge">{{ ev.date }}</div>
                    <div style="flex:1;">
                        <span class="genre-tag">#{{ ev.genre }}</span>
                        <div style="font-weight:700; font-size:1.2rem;">{{ ev.title }}</div>
                        <div style="color:#888; font-size:0.9rem;">📍 {{ ev.place }}</div>
                        <div style="margin-top:10px; font-size:0.95rem; white-space:pre-wrap;">{{ ev.detail }}</div>
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
    genre_filter = request.args.get('genre', 'all')
    all_events = load_events()
    
    if genre_filter != 'all':
        # 選んだジャンルだけを抜き出す
        filtered_events = [e for e in all_events if e.get('genre') == genre_filter]
    else:
        filtered_events = all_events
        
    return render_template_string(HTML_TEMPLATE, events=filtered_events, current_genre=genre_filter)

@app.route('/post', methods=['POST'])
def post():
    events = load_events()
    new_event = {
        "genre": request.form.get('genre'),
        "title": request.form.get('title'),
        "date": request.form.get('date'),
        "place": request.form.get('place'),
        "detail": request.form.get('detail')
    }
    events.insert(0, new_event)
    save_events(events)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)