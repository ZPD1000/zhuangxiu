# 装修记账 GitHub 同步指南

## 📋 配置步骤

### 1️⃣ 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名：`decoration-tracker`（或你喜欢的名字）
3. 设为 **Public**（公开）
4. 勾选 "Add a README file"
5. 点击 "Create repository"

### 2️⃣ 配置 Git 用户信息

```bash
# 替换为你的 GitHub 用户名和邮箱
git config --global user.name "你的 GitHub 用户名"
git config --global user.email "你的 GitHub 邮箱"
```

### 3️⃣ 生成 SSH 密钥

```bash
# 生成密钥（一路回车即可）
ssh-keygen -t ed25519 -C "你的 GitHub 邮箱"

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

**复制输出的内容**，然后：
1. 访问 https://github.com/settings/keys
2. 点击 "New SSH key"
3. 粘贴公钥内容
4. 点击 "Add SSH key"

### 4️⃣ 关联远程仓库

```bash
cd /home/admin/.openclaw/workspace

# 添加远程仓库（替换为你的仓库地址）
git remote add origin git@github.com:你的用户名/decoration-tracker.git

# 首次推送
git add .
git commit -m "初始化装修记账数据"
git branch -M main
git push -u origin main
```

### 5️⃣ 以后每次同步

```bash
# 运行同步脚本（自动更新网页 + Git 提交）
python3 /home/admin/.openclaw/workspace/装修/sync_expense.py
```

---

## 🌐 启用 GitHub Pages（在线访问）

1. 访问你的仓库：https://github.com/你的用户名/decoration-tracker
2. 点击 **Settings** → **Pages**
3. Source 选择 **main 分支** / **/root** 文件夹
4. 点击 **Save**
5. 等待几分钟后，访问：`https://你的用户名.github.io/decoration-tracker/装修/expense-report.html`

---

## 📁 同步的文件

| 文件 | 说明 |
|------|------|
| 装修/装修支出记录表.csv | 原始数据 |
| 装修/装修进度跟踪表.md | 进度记录 |
| 装修/expense-report.html | 生成的网页 |

---

## ⏰ 自动同步（可选）

设置每天凌晨 2 点自动同步：

```bash
crontab -e

# 添加以下行：
0 2 * * * cd /home/admin/.openclaw/workspace && /usr/bin/python3 /home/admin/.openclaw/workspace/装修/sync_expense.py >> /tmp/sync.log 2>&1
```

---

## ❓ 常见问题

### Q: 推送失败怎么办？
A: 检查：
1. SSH 密钥是否正确添加
2. 仓库地址是否正确
3. 运行 `ssh -T git@github.com` 测试连接

### Q: 网页在 GitHub Pages 打不开？
A: 确保：
1. Pages 已启用
2. 文件路径正确（GitHub Pages 区分大小写）
3. 等待 1-2 分钟生效

### Q: 如何查看同步状态？
A: 运行：
```bash
cd /home/admin/.openclaw/workspace
git status
git log --oneline -5
```

---

## 📞 需要帮助？

运行以下命令检查配置状态：
```bash
bash /home/admin/.openclaw/workspace/check-github-setup.sh
```
