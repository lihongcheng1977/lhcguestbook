import os
import json
import time
import base64
import smtplib
import requests
import markdown
from PIL import Image, ImageOps
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
from flask import Flask, render_template, request, redirect, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "fixed_2026_key_never_change"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_DIR, 'uploads')
MSG_UPLOAD_FOLDER = os.path.join(STATIC_DIR, 'msg_uploads')
CSS_FOLDER = os.path.join(STATIC_DIR, 'css')

# 确保所有目录存在（兼容持久化挂载）
for dir_path in [DATA_DIR, STATIC_DIR, UPLOAD_FOLDER, MSG_UPLOAD_FOLDER, CSS_FOLDER]:
    os.makedirs(dir_path, exist_ok=True)

MSG_FILE = os.path.join(DATA_DIR, 'messages.json')
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
LOG_FILE = os.path.join(DATA_DIR, 'email_logs.json')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
MAX_IMG_SIZE = 2 * 1024 * 1024
MAX_IMG_COUNT = 4
LOGO_SIZE = (200, 200)

# ==================== 初始化函数 ====================
def init_config_file():
    default_config = {
        "title": "留言板",
        "admin_password": generate_password_hash("123456"),
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "send_email": "",
        "send_email_pwd": "",
        "recv_email": "",
        "copyright_logo": "",
        "copyright_link": "",
        "copyright_text": "© 2026 留言板 版权所有",
        # 新增：默认可见开关（默认不勾选）
        "default_visible": False
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

def init_msg_file():
    if not os.path.exists(MSG_FILE):
        with open(MSG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def init_log_file():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def init_css():
    css_content = """
* {margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft Yahei",sans-serif;}
html,body {background:#f8f9fa;color:#333;line-height:1.6;min-height:100vh;display:flex;flex-direction:column;}
.container {max-width:1200px;min-width:320px;width:100%;margin:0 auto;flex:1;padding:0 20px;}
h1 {text-align:center;color:#4CAF50;margin:30px 0;}
.flash {padding:12px;background:#e8f5e9;color:#2e7d32;border-radius:8px;margin-bottom:20px;text-align:center;}

.btn {
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s;
    height: 36px;
    line-height: 20px;
    min-width: 90px;
    text-align: center;
}
.btn-purple {background: #6f42c1; color: white;}
.btn-green {background: #28a745; color: white;}
.btn-red {background: #dc3545; color: white;}
.btn-gray {background: #6c757d; color: white;}
.btn-blue {background: #007bff; color: white;}
.btn-orange {background: #fd7e14; color: white;}
.btn-default {background: #4CAF50; color: white;}
.btn-default:hover {background: #43a047;}

.btn-group {display:flex;gap:8px;align-items:center;margin:10px 0;flex-wrap:wrap;}
.form-control {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    height: 36px;
    line-height: 20px;
    font-size: 14px;
}
.card {background:white;padding:30px;border-radius:10px;box-shadow:0 3px 10px rgba(0,0,0,0.08);margin-bottom:30px;}
.form-group {margin-bottom:20px;}
.form-group label {font-weight:bold;margin-bottom:8px;display:block;}

.message-item {background:white;padding:25px;border-radius:10px;box-shadow:0 3px 10px rgba(0,0,0,0.08);margin-bottom:20px;}
.message-header {display:flex;justify-content:space-between;border-bottom:1px solid #eee;padding-bottom:10px;margin-bottom:15px;}
.message-content {background:#f9f9f9;padding:15px;border-radius:8px;}
.msg-images {display:flex;gap:10px;margin:10px 0;flex-wrap:wrap;}
.msg-image-item {width:150px;height:150px;}
.msg-image-item img {width:100%;height:100%;object-fit:cover;border-radius:8px;}

.login-box {max-width:400px;margin:50px auto;background:white;padding:40px;border-radius:10px;box-shadow:0 3px 20px rgba(0,0,0,0.1);width:100%;}
.login-box h1 {margin-bottom:30px;}

.emoji-panel {display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;}
.emoji-btn {background:transparent;border:none;font-size:22px;cursor:pointer;padding:4px;}

/* 图片预览样式 */
.upload-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 10px;
}
.preview-item {
    position: relative;
    width: 100px;
    height: 100px;
    border-radius: 8px;
    overflow: hidden;
}
.preview-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.preview-item .delete-btn {
    position: absolute;
    top: 5px;
    right: 5px;
    width: 20px;
    height: 20px;
    background: rgba(255, 255, 255, 0.8);
    border: none;
    border-radius: 50%;
    color: red;
    font-weight: bold;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    font-size: 12px;
}

/* 页脚样式 */
.footer {
    text-align: center;
    padding: 20px 0;
    margin-top: 30px;
    border-top: 1px solid #eee;
}

@media (max-width:768px) {
    .container {padding:0 10px;}
    .message-header {flex-direction:column;align-items:flex-start;gap:8px;}
    .btn-group {flex-wrap:wrap;}
    .login-box {padding:20px;margin:20px auto;}
    .card {padding:20px;}
    .message-item {padding:20px;}
}
"""
    css_file = os.path.join(CSS_FOLDER, 'global.css')
    if not os.path.exists(css_file):
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content.strip())

# ==================== 工具函数 ====================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_client_ip():
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        return '220.181.38.148' if ip in ['127.0.0.1', '::1'] else ip
    except:
        return '127.0.0.1'

def get_ip_location(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=3).json()
        if res.get("status") == "success":
            return f"{res.get('country', '')}-{res.get('regionName', '')}-{res.get('city', '')}"
        return "未知位置"
    except:
        return "未知位置"

def render_markdown(content):
    try:
        return markdown.markdown(content, extensions=['extra', 'nl2br'])
    except:
        return content

def compress_logo(image_path):
    try:
        with Image.open(image_path) as img:
            img = ImageOps.fit(img, LOGO_SIZE, Image.Resampling.LANCZOS)
            img.save(image_path, quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"压缩LOGO失败: {e}")
        return False

def save_base64_image(base64_str, filename):
    try:
        if ',' in base64_str:
            base64_data = base64_str.split(',')[1]
        else:
            base64_data = base64_str
        img_data = base64.b64decode(base64_data)
        filepath = os.path.join(MSG_UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(img_data)
        if os.path.getsize(filepath) <= MAX_IMG_SIZE:
            return f"/static/msg_uploads/{filename}"
        else:
            os.remove(filepath)
            return None
    except Exception as e:
        print(f"保存Base64图片失败: {e}")
        return None

def send_notify_email(msg_id, name, content, img_paths=[]):
    config = load_config()
    if not all([config.get('send_email'), config.get('send_email_pwd'), config.get('recv_email')]):
        add_email_log(msg_id, name, False, "邮件配置未完善")
        return False, "邮件配置未完善"
    try:
        msg = MIMEMultipart('related')
        msg['From'] = Header(config['send_email'])
        msg['To'] = Header(config['recv_email'])
        msg['Subject'] = Header(f"【{config['title']}】新留言通知(ID:{msg_id})", 'utf-8')
        
        img_html = ""
        if img_paths:
            img_items = []
            for i in range(len(img_paths)):
                img_items.append(f'<div class="image-item"><img src="cid:{i}" alt="图片{i+1}"></div>')
            img_html = f'<div class="info-item"><span class="label">上传图片：</span></div><div class="images">{"".join(img_items)}</div>'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>新留言通知</title>
            <style>
                body {{font-family:"Microsoft Yahei", sans-serif;line-height:1.8;background:#f5f5f5;margin:0;padding:20px;}}
                .container {{max-width:600px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}}
                h2 {{color:#333;border-bottom:2px solid #4CAF50;padding-bottom:10px;margin-bottom:20px;}}
                .info-item {{margin:10px 0;font-size:16px;}}
                .label {{font-weight:bold;color:#555;display:inline-block;width:80px;}}
                .content {{background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;white-space:pre-wrap;}}
                .images {{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;}}
                .image-item {{width:120px;height:120px;border-radius:8px;overflow:hidden;}}
                .image-item img {{width:100%;height:100%;object-fit:cover;}}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>新留言通知</h2>
                <div class="info-item"><span class="label">留言ID：</span>{msg_id}</div>
                <div class="info-item"><span class="label">留言人：</span>{name or '匿名用户'}</div>
                <div class="info-item"><span class="label">留言时间：</span>{time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div class="info-item"><span class="label">IP地址：</span>{get_client_ip()} ({get_ip_location(get_client_ip())})</div>
                <div class="info-item"><span class="label">留言内容：</span></div>
                <div class="content">{render_markdown(content)}</div>
                {img_html}
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        for i, img_path in enumerate(img_paths):
            try:
                img_full_path = os.path.join(BASE_DIR, img_path.lstrip('/'))
                if os.path.exists(img_full_path):
                    with open(img_full_path, 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-ID', f'<{i}>')
                        msg.attach(img)
            except Exception as e:
                print(f"附加图片{i}失败: {e}")
        server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], timeout=15)
        server.login(config['send_email'], config['send_email_pwd'])
        server.sendmail(config['send_email'], config['recv_email'], msg.as_string())
        server.quit()
        add_email_log(msg_id, name, True, "邮件发送成功")
        return True, "邮件发送成功"
    except Exception as e:
        error_msg = f"邮件发送失败：{str(e)}"
        print(error_msg)
        add_email_log(msg_id, name, False, error_msg)
        return False, error_msg

def add_email_log(msg_id, name, success, msg):
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        logs.append({
            "msg_id": msg_id,
            "name": name,
            "time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "success": success,
            "message": msg
        })
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"添加邮件日志失败: {e}")

# ==================== 配置/数据操作函数 ====================
def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        init_config_file()
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def save_config(new_config):
    try:
        old_config = load_config()
        for key, value in old_config.items():
            if key not in new_config:
                new_config[key] = value
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False

def load_messages():
    try:
        with open(MSG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        init_msg_file()
        return []

def save_messages(messages):
    try:
        with open(MSG_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存留言失败: {e}")
        return False

def save_message(name, content, img_paths):
    try:
        messages = load_messages()
        # 读取默认可见配置
        config = load_config()
        default_visible = config.get("default_visible", False)
        
        new_msg = {
            "id": int(time.time()),
            "name": name or "匿名用户",
            "content": content,
            "content_html": render_markdown(content),
            "images": img_paths,
            "time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "ip": get_client_ip(),
            "location": get_ip_location(get_client_ip()),
            "likes": 0,
            "replies": [],
            # 使用配置中的默认可见状态
            "visible": default_visible
        }
        messages.insert(0, new_msg)
        save_messages(messages)
        return new_msg["id"]
    except Exception as e:
        print(f"保存单条留言失败: {e}")
        return None

def delete_message(msg_id):
    try:
        messages = load_messages()
        for msg in messages:
            if msg["id"] == int(msg_id):
                # 删除留言关联的图片
                for img_path in msg.get("images", []):
                    try:
                        full_path = os.path.join(BASE_DIR, img_path.lstrip('/'))
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    except:
                        pass
                break
        messages = [msg for msg in messages if msg["id"] != int(msg_id)]
        save_messages(messages)
        # 删除关联的邮件日志
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            logs = [log for log in logs if str(log.get('msg_id', '')) != str(msg_id)]
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"删除留言失败: {e}")
        return False

def add_reply(msg_id, reply_content):
    try:
        messages = load_messages()
        for msg in messages:
            if msg["id"] == int(msg_id):
                msg["replies"].append({
                    "id": int(time.time()),
                    "content": reply_content,
                    "content_html": render_markdown(reply_content),
                    "time": time.strftime('%Y-%m-%d %H:%M:%S')
                })
                save_messages(messages)
                return True
        return False
    except Exception as e:
        print(f"添加回复失败: {e}")
        return False

def add_like(msg_id):
    try:
        messages = load_messages()
        updated = False
        for msg in messages:
            if msg["id"] == int(msg_id):
                msg["likes"] = msg.get("likes", 0) + 1
                updated = True
                break
        if updated:
            save_messages(messages)
            return True
        return False
    except Exception as e:
        print(f"点赞失败: {e}")
        return False

def set_like_count(msg_id, count):
    try:
        messages = load_messages()
        for msg in messages:
            if msg["id"] == int(msg_id):
                msg["likes"] = int(count)
                save_messages(messages)
                return True
        return False
    except Exception as e:
        print(f"设置点赞数失败: {e}")
        return False

def toggle_visible(msg_id):
    try:
        messages = load_messages()
        for msg in messages:
            if msg["id"] == int(msg_id):
                msg["visible"] = not msg.get("visible", False)
                save_messages(messages)
                return True, msg["visible"]
        return False, False
    except Exception as e:
        print(f"切换显示状态失败: {e}")
        return False, False

# ==================== 路由 ====================
@app.route('/', methods=['GET', 'POST'])
def index():
    config = load_config()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        content = request.form.get('content', '').strip()
        if not content:
            flash('❌ 留言内容不能为空！')
        else:
            img_paths = []
            # 修复：正确读取图片数据（allImagesInput）
            all_images_str = request.form.get('allImagesInput', '')
            if all_images_str:
                try:
                    selected_images = json.loads(all_images_str)
                    selected_images = selected_images[:MAX_IMG_COUNT]
                    for i, img in enumerate(selected_images):
                        if img and img.get('base64'):
                            ext = img['name'].split('.')[-1].lower() if '.' in img['name'] else 'jpg'
                            filename = f"msg_{int(time.time())}_{i}.{ext}"
                            img_path = save_base64_image(img['base64'], filename)
                            if img_path:
                                img_paths.append(img_path)
                    if len(img_paths) > 0:
                        flash(f'✅ 成功上传 {len(img_paths)} 张图片')
                    if len(selected_images) > len(img_paths):
                        flash(f'⚠️ 有 {len(selected_images)-len(img_paths)} 张图片保存失败（可能超出2M）')
                except Exception as e:
                    flash(f'❌ 图片处理失败: {str(e)}')
            msg_id = save_message(name, content, img_paths)
            if msg_id:
                send_notify_email(msg_id, name, content, img_paths)
                # 根据默认可见状态提示
                if config.get("default_visible", False):
                    flash('✅ 留言提交成功！已在前台显示')
                else:
                    flash('✅ 留言提交成功！管理员审核后将显示')
                return redirect('/')
            else:
                flash('❌ 留言保存失败，请重试！')
    messages = load_messages()
    visible_messages = [msg for msg in messages if msg.get('visible', False)]
    return render_template(
        'index.html',
        title=config['title'],
        messages=visible_messages,
        copyright_logo=config.get('copyright_logo', ''),
        copyright_link=config.get('copyright_link', ''),
        copyright_text=config.get('copyright_text', '')
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    config = load_config()
    if session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        stored_pwd = config.get('admin_password', '')
        if check_password_hash(stored_pwd, password):
            session['admin'] = True
            flash('✅ 登录成功！')
            return redirect('/admin')
        else:
            flash('❌ 密码错误，请重试！')
    return render_template('login.html', title=f"{config['title']} - 管理员登录")

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('✅ 已成功退出登录！')
    return redirect('/login')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect('/login')
    config = load_config()
    if request.method == 'POST':
        if 'reply_msg' in request.form and 'reply_content' in request.form:
            msg_id = request.form.get('reply_msg')
            reply_content = request.form.get('reply_content').strip()
            if reply_content:
                if add_reply(msg_id, reply_content):
                    flash('✅ 回复添加成功！')
                else:
                    flash('❌ 回复添加失败！')
        elif 'delete_msg' in request.form:
            msg_id = request.form.get('delete_msg')
            if delete_message(msg_id):
                flash('✅ 留言删除成功！')
            else:
                flash('❌ 留言删除失败！')
        elif 'set_like' in request.form and 'like_count' in request.form:
            msg_id = request.form.get('set_like')
            like_count = request.form.get('like_count', 0)
            if set_like_count(msg_id, like_count):
                flash('✅ 点赞数修改成功！')
            else:
                flash('❌ 点赞数修改失败！')
        elif 'save_config' in request.form:
            # 修复：正确读取checkbox状态，一次保存生效
            default_visible = request.form.get('default_visible') == 'on'
            new_config = {
                "title": request.form.get('title', config['title']).strip(),
                "admin_password": config['admin_password'],
                "smtp_server": request.form.get('smtp_server', config['smtp_server']).strip(),
                "smtp_port": int(request.form.get('smtp_port', config['smtp_port']) or 465),
                "send_email": request.form.get('send_email', config['send_email']).strip(),
                "send_email_pwd": request.form.get('send_email_pwd', config['send_email_pwd']).strip(),
                "recv_email": request.form.get('recv_email', config['recv_email']).strip(),
                "copyright_link": request.form.get('copyright_link', config['copyright_link']).strip(),
                "copyright_text": request.form.get('copyright_text', config['copyright_text']).strip(),
                "copyright_logo": config['copyright_logo'],
                # 正确保存开关状态
                "default_visible": default_visible
            }
            # 处理LOGO上传
            logo_file = request.files.get('copyright_logo')
            if logo_file and logo_file.filename and allowed_file(logo_file.filename):
                filename = secure_filename(f"logo_{int(time.time())}.{logo_file.filename.rsplit('.', 1)[1].lower()}")
                logo_path = os.path.join(UPLOAD_FOLDER, filename)
                logo_file.save(logo_path)
                compress_logo(logo_path)
                new_config['copyright_logo'] = f"/static/uploads/{filename}"
            if save_config(new_config):
                flash('✅ 系统配置保存成功！')
            else:
                flash('❌ 系统配置保存失败！')
    if request.args.get('toggle_visible'):
        msg_id = request.args.get('toggle_visible')
        success, status = toggle_visible(msg_id)
        if success:
            flash('✅ 留言已%s！' % ('显示' if status else '隐藏'))
        else:
            flash('❌ 操作失败！')
        return redirect(f'/admin#msg-{msg_id}')
    messages = load_messages()
    return render_template(
        'admin.html',
        title=f"{config['title']} - 后台管理",
        config=config,
        messages=messages
    )

@app.route('/admin/logs/<msg_id>')
def admin_msg_logs(msg_id):
    if not session.get('admin'):
        return redirect('/login')
    config = load_config()
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    msg_logs = [log for log in logs if str(log.get('msg_id', '')) == str(msg_id)]
    return render_template('msg_logs.html', title=f"{config['title']} - 留言{msg_id}日志", logs=msg_logs, msg_id=msg_id)

@app.route('/admin/logs')
def admin_logs():
    if not session.get('admin'):
        return redirect('/login')
    config = load_config()
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    return render_template('logs.html', title=f"{config['title']} - 邮件日志", logs=logs)

@app.route('/admin/change_pwd', methods=['POST'])
def change_pwd():
    if not session.get('admin'):
        return redirect('/login')
    config = load_config()
    old_pwd = request.form.get('old_pwd', '').strip()
    new_pwd = request.form.get('new_pwd', '').strip()
    confirm_pwd = request.form.get('confirm_pwd', '').strip()
    if not check_password_hash(config['admin_password'], old_pwd):
        flash('❌ 旧密码错误！')
    elif new_pwd != confirm_pwd:
        flash('❌ 两次输入的新密码不一致！')
    elif len(new_pwd) < 6:
        flash('❌ 新密码长度不能少于6位！')
    else:
        config['admin_password'] = generate_password_hash(new_pwd)
        save_config(config)
        flash('✅ 密码修改成功！请重新登录')
        session.pop('admin', None)
        return redirect('/login')
    return redirect('/admin')

@app.route('/like/<msg_id>')
def like(msg_id):
    if add_like(msg_id):
        referer = request.headers.get('Referer', '/')
        return redirect(referer)
    else:
        flash('❌ 点赞失败！')
        referer = request.headers.get('Referer', '/')
        return redirect(referer)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)

# ==================== 程序入口 ====================
if __name__ == "__main__":
    init_config_file()
    init_msg_file()
    init_log_file()
    init_css()
    print("🚀 留言板服务启动成功！")
    print("🌐 访问地址: http://0.0.0.0:5000")
    print("🔑 默认管理员密码: 123456")
    print("🔧 后台地址: http://0.0.0.0:5000/login")
    app.run(host='0.0.0.0', port=5000, debug=False)