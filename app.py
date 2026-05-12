import json
import os
import urllib.parse
import datetime
from flask import Flask, render_template_string, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- 設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'events.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ADMIN_PASSWORD = "soyoka_admin" 

def load_events():
    if not os.path.exists(JSON_PATH): return []
    with open(JSON_PATH, 'r', encoding='utf-8') as f: return json.load(f)

def save_events(events):
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

categories = [
    {'id': 'all', 'name': 'All / Mix', 'icon': 'all.png'},
    {'id': 'lesbian', 'name': 'Lesbian', 'icon': 'les.png'},
    {'id': 'gay', 'name': 'Gay', 'icon': 'gay.png'},
    {'id': 'bisexual', 'name': 'Bisexual', 'icon': 'bi.png'},
    {'id': 'transgender', 'name': 'Transgender', 'icon': 'trans.png'},
    {'id': 'queer', 'name': 'Queer', 'icon': 'queer.png'},
]

COMMON_STYLE = '''
<style>
    body { 
        background: linear-gradient(135deg, #fef1f2 0%, #fff5f7 100%); 
        font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
        color: #444; 
    }
    .nav-pills { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(5px); border-radius: 50px; padding: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); }
    .nav-link { color: #888; border-radius: 30px !important; transition: 0.3s; }
    .nav-link.active { background-color: #ff6b81 !important; box-shadow: 0 4px 10px rgba(255,107,129,0.3); }
    .card { border: none; border-radius: 24px; transition: all 0.3s cubic-bezier(.25,.8,.25,1); background: #fff; }
    .card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(255,107,129,0.1) !important; }
    .event-image { height: 220px; object-fit: cover; border-radius: 24px 24px 0 0; }
    .post-button {
        position: fixed; bottom: 30px; right: 30px; width: 65px; height: 65px;
        background: #ff6b81; color: #fff; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 30px; box-shadow: 0 8px 20px rgba(255,107,129,0.4); z-index: 1000; text-decoration: none;
        transition: 0.3s;
    }
    .post-button:hover { transform: scale(1.1) rotate(90deg); color: #fff; }
</style>
'''

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LGBTQ+ イベント掲示板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    ''' + COMMON_STYLE + '''
</head>
<body>
    <div class="container py-5">
        <h1 class="text-center fw-bold mb-5" style="color: #ff6b81;">🌈 LGBTQ+ Events</h1>
        <ul class="nav nav-pills justify-content-center mb-5">
            {% for cat in categories %}
            <li class="nav-item">
                <a class="nav-link {% if active_cat == cat.id %}active{% endif %}" href="/?category={{ cat.id }}">
                    <img src="/static/images/icon_{{ cat.icon }}" style="width:20px; margin-bottom:2px;"> {{ cat.name }}
                </a>
            </li>
            {% endfor %}
        </ul>
        <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
            {% for event in events %}
            <div class="col">
                <div class="card h-100 shadow-sm">
                    <a href="/event/{{ event.id }}"><img src="{{ event.image_url }}" class="card-img-top event-image"></a>
                    <div class="card-body p-4">
                        <div class="d-flex justify-content-between">
                            <span class="badge bg-light text-secondary rounded-pill mb-2">{{ event.category|capitalize }}</span>
                            <small class="text-muted"><i class="bi bi-chat-dots"></i> {{ event.comments|length }}</small>
                        </div>
                        <h5 class="card-title fw-bold"><a href="/event/{{ event.id }}" class="text-decoration-none text-dark">{{ event.title }}</a></h5>
                        <p class="small text-muted mb-4"><i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="d-flex flex-wrap gap-1">
                                {% for tag in event.tags %}<span class="badge bg-light text-pink rounded-pill" style="color:#ff6b81;">#{{ tag }}</span>{% endfor %}
                            </div>
                            <form action="/delete/{{ event.id }}" method="POST" style="display: inline;" 
                                  onsubmit="const pw = prompt('管理用パスワードを入力'); if(pw){ this.password.value = pw; return true; } return false;">
                                <input type="hidden" name="password" value="">
                                <button type="submit" class="btn text-muted p-0"><i class="bi bi-trash"></i></button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    <a href="/post" class="post-button"><i class="bi bi-plus-lg"></i></a>
</body>
</html>
'''

DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ event.title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    ''' + COMMON_STYLE + '''
</head>
<body>
    <div class="container py-5" style="max-width: 800px;">
        <div class="card shadow border-0 overflow-hidden mb-4" style="border-radius: 30px;">
            <img src="{{ event.image_url }}" class="img-fluid w-100" style="max-height: 450px; object-fit: cover;">
            <div class="card-body p-5">
                <div class="d-flex justify-content-between align-items-start mb-4">
                    <h1 class="fw-bold">{{ event.title }}</h1>
                    <a href="https://twitter.com/share?url={{ share_url }}&text={{ share_text }}" 
                       target="_blank" class="btn btn-dark rounded-pill px-4">
                        <i class="bi bi-twitter-x"></i> Share
                    </a>
                </div>
                <p class="text-muted"><i class="bi bi-calendar3"></i> {{ event.date }}　<i class="bi bi-geo-alt"></i> {{ event.location }}</p>
                <hr class="my-4">
                <p style="white-space: pre-wrap; line-height: 1.8;">{{ event.description or "詳細なし" }}</p>
                
                <div class="mt-5 pt-5 border-top">
                    <h5 class="fw-bold mb-4"><i class="bi bi-chat-left-text"></i> コメント ({{ event.comments|length }})</h5>
                    {% for comment in event.comments %}
                    <div class="bg-light p-3 rounded-4 mb-3">
                        <small class="text-muted d-block mb-1">{{ comment.date }}</small>
                        {{ comment.text }}
                    </div>
                    {% endfor %}
                    
                    <form action="/comment/{{ event.id }}" method="POST" class="mt-4">
                        <div class="input-group">
                            <input type="text" name="comment" class="form-control rounded-pill-start" placeholder="一言送る..." required>
                            <button class="btn btn-primary rounded-pill-end" style="background:#ff6b81; border:none;">送信</button>
                        </div>
                    </form>
                </div>
                
                <div class="mt-5 d-grid"><a href="/" class="btn btn-outline-secondary rounded-pill">掲示板に戻る</a></div>
            </div>
        </div>
    </div>
</body>
</html>
'''

# POST_TEMPLATE の select 部分を修正
POST_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><title>投稿</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    ''' + COMMON_STYLE + '''
</head>
<body>
    <div class="container py-5" style="max-width: 600px;">
        <div class="card p-5 shadow-sm">
            <h2 class="mb-4 fw-bold">New Event</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3"><label class="form-label">タイトル</label><input type="text" name="title" class="form-control" required></div>
                <div class="mb-3"><label class="form-label">カテゴリ</label>
                    <select name="category" class="form-select">
                        {% for cat in categories %}
                        <option value="{{ cat.id }}">{{ cat.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-3"><label class="form-label">日付 / 場所</label>
                    <div class="row g-2">
                        <div class="col"><input type="text" name="date" class="form-control" placeholder="日付"></div>
                        <div class="col"><input type="text" name="location" class="form-control" placeholder="場所"></div>
                    </div>
                </div>
                <div class="mb-3"><label class="form-label">詳細</label><textarea name="description" class="form-control" rows="4"></textarea></div>
                <div class="mb-3"><label class="form-label">画像</label><input type="file" name="image" class="form-control" accept="image/*"></div>
                <div class="mb-3"><label class="form-label">タグ (カンマ区切り)</label><input type="text" name="tags" class="form-control"></div>
                <button type="submit" class="btn btn-primary w-100 py-3 rounded-pill fw-bold" style="background:#ff6b81; border:none;">公開する</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    all_events = load_events()
    active_cat = request.args.get('category', 'all')
    events = all_events if active_cat == 'all' else [e for e in all_events if e['category'] == active_cat]
    return render_template_string(INDEX_TEMPLATE, events=events, categories=categories, active_cat=active_cat)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        events = load_events()
        image_file = request.files.get('image')
        image_url = "https://via.placeholder.com/500x300"
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = '/static/uploads/' + filename

        new_event = {
            "id": int(os.urandom(4).hex(), 16),
            "category": request.form.get('category'),
            "title": request.form.get('title'),
            "description": request.form.get('description'),
            "date": request.form.get('date'),
            "location": request.form.get('location'),
            "image_url": image_url,
            "tags": [t.strip() for t in request.form.get('tags').split(',')] if request.form.get('tags') else [],
            "comments": []
        }
        events.append(new_event)
        save_events(events)
        return redirect(url_for('index'))
    # ここで if cat.id != 'all' を削除した全カテゴリを渡します
    return render_template_string(POST_TEMPLATE, categories=categories)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    events = load_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    if event is None: return "NotFound", 404
    share_text = urllib.parse.quote(f"🌈 LGBTQ+ イベント：{event['title']}")
    share_url = urllib.parse.quote(request.url)
    return render_template_string(DETAIL_TEMPLATE, event=event, share_text=share_text, share_url=share_url)

@app.route('/comment/<int:event_id>', methods=['POST'])
def add_comment(event_id):
    events = load_events()
    comment_text = request.form.get('comment')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    for e in events:
        if e.get('id') == event_id:
            if 'comments' not in e: e['comments'] = []
            e['comments'].append({"text": comment_text, "date": now})
            break
    save_events(events)
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if request.form.get('password') == ADMIN_PASSWORD:
        events = load_events()
        save_events([e for e in events if e.get('id') != event_id])
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)