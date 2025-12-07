# GitHub 連接與上傳指南

## 當前狀態
✅ 遠程倉庫已設置：`https://github.com/kgwlove/2025_10_26_chihlee_pi_pico.git`
⚠️ Git 用戶名和郵箱尚未配置
📝 有 3 個文件已暫存，等待提交

## 步驟 1：配置 Git 用戶資訊

在 PowerShell 中執行以下命令（請替換為您的實際資訊）：

```bash
git config --global user.name "您的GitHub用戶名"
git config --global user.email "您的GitHub郵箱"
```

例如：
```bash
git config --global user.name "kgwlove"
git config --global user.email "your-email@example.com"
```

## 步驟 2：設置 GitHub 認證

GitHub 已不再支持使用密碼進行 Git 操作，需要使用 **Personal Access Token (PAT)**。

### 2.1 創建 Personal Access Token

1. 登入 GitHub
2. 點擊右上角頭像 → **Settings**
3. 左側選單最下方 → **Developer settings**
4. 點擊 **Personal access tokens** → **Tokens (classic)**
5. 點擊 **Generate new token** → **Generate new token (classic)**
6. 填寫：
   - **Note**: 例如 "Cursor Git Access"
   - **Expiration**: 選擇過期時間（建議 90 天或更長）
   - **Select scopes**: 勾選 `repo`（完整倉庫權限）
7. 點擊 **Generate token**
8. **重要**：複製生成的 token（只會顯示一次！）

### 2.2 使用 Token 進行認證

當您執行 `git push` 時，系統會要求輸入：
- **Username**: 您的 GitHub 用戶名
- **Password**: 貼上剛才複製的 Personal Access Token（不是您的 GitHub 密碼）

## 步驟 3：提交並推送代碼

### 3.1 提交已暫存的文件

```bash
git commit -m "新增 lesson7: WiFi 連接和 MQTT 功能"
```

### 3.2 推送到 GitHub

```bash
git push origin master
```

如果這是第一次推送，系統會要求輸入認證資訊：
- Username: 您的 GitHub 用戶名
- Password: 您的 Personal Access Token

## 步驟 4：驗證推送成功

推送完成後，可以：
1. 訪問 `https://github.com/kgwlove/2025_10_26_chihlee_pi_pico` 查看倉庫
2. 確認 lesson7 文件夾已出現在 GitHub 上

## 常見問題

### Q: 如何保存認證資訊，避免每次都要輸入？
A: 可以使用 Git Credential Manager 或配置 credential helper：

```bash
# 使用 Windows Credential Manager（推薦）
git config --global credential.helper wincred
```

### Q: 如果推送時出現認證錯誤怎麼辦？
A: 
1. 確認 Personal Access Token 是否正確複製
2. 確認 Token 的權限包含 `repo`
3. 確認 Token 尚未過期
4. 可以重新生成新的 Token

### Q: 如何檢查當前配置？
A:
```bash
git config --global --list
git remote -v
```

## 快速命令參考

```bash
# 配置用戶資訊
git config --global user.name "您的用戶名"
git config --global user.email "您的郵箱"

# 提交更改
git commit -m "提交訊息"

# 推送到 GitHub
git push origin master

# 查看狀態
git status
```

