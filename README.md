                                      lhcguestbook


一、推荐编辑 README.md 的软件
你可以用以下任意一种工具来编辑，都非常适合写 Markdown：
VS Code（免费、跨平台，最推荐）
安装 Markdown 插件（如 Markdown All in One），可以实时预览、语法高亮、一键格式化。
直接打开项目里的 README.md，写完后 Ctrl+S 保存即可。
Typora（所见即所得，直观易用）
可视化编辑，写完就是最终渲染效果，适合新手。
GitHub 网页端（无需安装软件，直接在线改）
打开你的仓库 https://github.com/lihongcheng1977/lhcguestbook → 点击 README.md → 点击 ✏️ 编辑按钮，直接在线写，写完提交即可。
二、完整可直接使用的 README.md 内容
下面是已经帮你写好、包含图片引用的完整版本，你可以直接复制到 README.md 文件里：
markdown
# 轻量级留言板（Docker一键部署版）
基于 Flask + SQLite + Docker 的极简留言板系统，支持邮件通知、后台可视化配置、留言管理，开箱即用，适合个人站点或小型场景使用。

---

## ✨ 项目展示
### 前台留言页面
![前台留言页面](https://raw.githubusercontent.com/lihongcheng1977/lhcguestbook/main/你的前台页面截图文件名.png)

- 简洁的留言提交界面，包含姓名和留言内容输入框
- 实时展示历史留言列表，带时间戳
- 防重复提交设计，刷新页面不会重复发送邮件

### 后台管理页面
![后台管理页面](https://raw.githubusercontent.com/lihongcheng1977/lhcguestbook/main/你的后台页面截图文件名.png)

- 可视化配置面板，支持修改页面标题、管理员密码、邮箱配置等
- 局部更新机制：无需修改全部配置，仅填写需要变更的项即可
- 留言管理：支持查看邮件发送日志、删除无用留言
- 安全机制：1分钟无操作自动登出，保护后台权限

---

## 🚀 功能特性
| 功能 | 说明 |
|------|------|
| 前台留言 | 访客可提交姓名和留言，实时展示 |
| 后台管理 | 管理员可登录修改配置、管理留言 |
| 邮件通知 | 新留言自动发送邮件提醒（适配QQ/163等主流邮箱） |
| 配置可视化 | 后台直接修改所有配置项，无需手动编辑JSON文件 |
| 防重复提交 | 采用PRG模式，刷新页面不会重复发送邮件 |
| 数据持久化 | 支持挂载配置文件和数据库，容器重启数据不丢失 |
| 安全防护 | 1分钟无操作自动登出，密码/授权码输入框隐藏显示 |

---

## 📦 快速部署（Docker 推荐）
### 方式1：拉取镜像部署（最简单）
```bash
# 1. 拉取最新镜像
docker pull wwwlhc/lhcguestbook:latest

# 2. 启动容器（持久化配置+数据库，避免数据丢失）
docker run -d \
  -p 8898:5000 \
  --name lhcguestbook \
  -v /你的本地路径/config.json:/app/config.json \
  -v /你的本地路径/messages.db:/app/messages.db \
  wwwlhc/lhcguestbook:latest
方式 2：从源码构建
bash
运行
# 1. 克隆代码
git clone https://github.com/lihongcheng1977/lhcguestbook.git
cd lhcguestbook

# 2. 构建镜像
docker build -t lhcguestbook:latest .

# 3. 启动容器
docker run -d -p 8898:5000 --name lhcguestbook lhcguestbook:latest
🔗 访问地址
启动容器后，通过以下地址访问：
前台留言页：http://你的服务器IP:8898
后台登录页：http://你的服务器IP:8898/login
初始管理员密码：123456（建议登录后立即修改）
后台管理页：登录后自动跳转，可修改配置、管理留言
⚙️ 配置说明
邮箱配置（以 QQ 邮箱为例）
在后台管理页填写以下信息，即可开启邮件通知：
SMTP 服务器：smtp.qq.com
SMTP 端口：465
发送邮箱：你的 QQ 邮箱（如 xxx@qq.com）
邮箱授权码：QQ 邮箱设置 → 账户 → 开启 POP3/IMAP/SMTP → 生成授权码
接收邮箱：可填写与发送邮箱相同的地址
配置更新规则
所有输入框默认加载当前配置，不修改请留空
仅填写需要变更的项，点击「保存配置」即可生效
端口号仅允许数字，邮箱地址必须包含 @ 符号
📂 项目结构
plaintext
lhcguestbook/
├── app.py                 # 核心业务逻辑（Flask 后端）
├── config.json            # 配置文件（可挂载持久化）
├── messages.db            # SQLite 数据库（可挂载持久化）
├── requirements.txt       # Python 依赖清单
├── Dockerfile             # Docker 构建脚本
├── templates/             # 前端模板
│   ├── index.html         # 前台留言页面
│   ├── admin.html         # 后台管理页面
│   └── login.html         # 后台登录页面
└── README.md              # 项目说明文档
🛠️ 常见问题
1. 无法访问页面？
检查 Docker 端口映射是否正确：docker ps
确认容器正常运行：docker start lhcguestbook
查看容器日志排查问题：docker logs lhcguestbook
2. 邮件发送失败？
确认邮箱 SMTP 服务已开启，授权码正确
后台点击「邮件日志」按钮，查看具体失败原因
QQ/163 邮箱需使用 SSL 端口（465），不要使用 587 或 25
3. 数据丢失？
启动容器时必须使用 -v 参数挂载 config.json 和 messages.db
若未挂载，容器删除后所有配置和留言数据将丢失
📝 更新日志
v1.0：初始版本，支持留言提交、邮件通知、后台配置管理、Docker 一键部署
📄 开源协议
本项目采用 MIT 协议开源，可自由使用、修改和分发。
🤝 贡献
欢迎提交 Issue 或 Pull Request 来完善项目！
plaintext

### 三、关于图片引用的说明
1.  把你这两张截图分别命名为：
    - 前台页：`index_page.png`
    - 后台页：`admin_page.png`
2.  把这两张图片放到项目根目录（和 `app.py` 同级）
3.  把上面 README 里的图片链接替换成：
    ```markdown
    ![前台留言页面](https://raw.githubusercontent.com/lihongcheng1977/lhcguestbook/main/index_page.png)
    ![后台管理页面](https://raw.githubusercontent.com/lihongcheng1977/lhcguestbook/main/admin_page.png)
把图片和 README 一起提交到 GitHub：
bash
运行
git add .
git commit -m "添加README和页面截图"
git push origin main