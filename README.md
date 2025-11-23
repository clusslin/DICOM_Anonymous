# DICOM 匿名化平台

一個功能完整的 DICOM 影像匿名化網頁平台，可從指定的 DICOM 伺服器下載影像，進行匿名化處理後提供下載。

## 功能特點

### 核心功能
- **DICOM 伺服器管理**：支援多個 DICOM 伺服器配置，可設定連線參數並測試連線
- **病人查詢**：支援多條件查詢（病人姓名、ID、檢查日期、檢查類型等）
- **Series 詳細資訊**：查詢結果詳列每個 Study 的 Series 資訊
- **批次匿名化**：可一次選擇多筆影像進行匿名化，系統依序處理
- **彈性匿名化選項**：使用者可自訂要移除或保留的 DICOM 標籤
- **保持原始格式**：匿名化後保持原始傳輸語法（包括 JPEG2000 壓縮格式）

### 管理功能
- **使用者管理**：管理員可新增、編輯、刪除使用者
- **權限控制**：區分一般使用者與管理員權限
- **伺服器配置**：在管理介面設定 DICOM 伺服器連線資訊

### 安全性
- JWT Token 認證
- 密碼加密儲存
- 可設定匿名化規則符合 DICOM PS3.15 Annex E

## 技術架構

### 後端
- **Python 3.11+**
- **FastAPI** - 高效能 API 框架
- **SQLAlchemy** - 非同步 ORM
- **pydicom** - DICOM 檔案處理
- **pynetdicom** - DICOM 網路通訊 (C-ECHO, C-FIND, C-GET/C-MOVE)

### 前端
- **Vue.js 3** - 漸進式 JavaScript 框架
- **Element Plus** - Vue 3 UI 元件庫
- **Pinia** - 狀態管理
- **Vite** - 建置工具

### 部署
- **Docker** - 容器化部署
- **Nginx** - 反向代理

## 快速開始

### 使用 Docker Compose（建議）

1. 複製專案
```bash
git clone <repository-url>
cd DICOM_Anonymous
```

2. 複製並修改環境變數
```bash
cp .env.example .env
# 編輯 .env 設定密鑰和管理員密碼
```

3. 啟動服務
```bash
docker-compose up -d
```

4. 開啟瀏覽器訪問 `http://localhost`

### 本地開發

#### 後端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 前端
```bash
cd frontend
npm install
npm run dev
```

## 預設帳號

- 使用者名稱：`admin`
- 密碼：`admin123`

**請在生產環境中修改預設密碼！**

## API 文件

啟動後端服務後，可訪問：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## DICOM 伺服器設定

在管理介面中設定 DICOM 伺服器：

| 參數 | 說明 |
|------|------|
| 名稱 | 伺服器顯示名稱 |
| 主機 | IP 位址或域名 |
| Port | DICOM 服務埠號（預設 104）|
| AE Title | 遠端 AE Title |
| 本地 AE Title | 本系統的 AE Title |
| 支援 C-GET | 若伺服器支援 C-GET 則使用，否則使用 C-MOVE |

## 匿名化選項

系統提供以下匿名化選項，使用者可根據需求選擇：

### 病人資訊
- 移除/替換病人姓名
- 移除/替換病人ID
- 移除出生日期
- 移除地址
- 移除電話號碼

### 機構/醫師資訊
- 移除機構名稱
- 移除醫師姓名

### 其他
- 移除私有標籤
- 保留/移除檢查日期
- 保留/移除檢查描述
- UID 雜湊處理

## 注意事項

1. **JPEG2000 格式保持**：系統會保持原始的傳輸語法，不會對壓縮影像進行解壓縮
2. **UID 一致性**：同一批次匿名化會維持 UID 的參照完整性
3. **批次處理**：大量影像會依序處理，請耐心等待
4. **儲存空間**：請確保有足夠的磁碟空間存放暫存檔案

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！
