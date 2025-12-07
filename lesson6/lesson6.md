# Lesson6 Flask 專案程式邏輯分析

## 📋 專案概述

Lesson6 是一個基於 Flask 的 MQTT 感測器監控應用程式，用於即時顯示和記錄感測器數據（溫度、濕度、電燈狀態）。專案採用 Flask + Socket.IO 架構，提供 WebSocket 即時推送功能。

---

## 🏗️ 專案架構

### 檔案結構

```
lesson6/
├── app_flask.py              # Flask 主應用程式（核心檔案）
├── templates/
│   └── index.html           # 前端網頁介面
├── generate_test_data.py    # 測試數據生成工具
├── test_mqtt_publish.py     # MQTT 測試發布工具
├── sensor_data.csv          # CSV 格式數據檔案
├── sensor_data.xlsx         # Excel 格式數據檔案
├── start.sh                 # 啟動腳本
└── app.py                   # 已棄用的 Streamlit 版本
```

---

## 🔄 程式邏輯流程分析

### 1. 應用程式啟動流程

#### 1.1 初始化階段（`app_flask.py` 第 15-35 行）

```python
# Flask 應用程式初始化
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# MQTT 設定（可修改）
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "客廳/感測器"

# 全域數據儲存
sensor_data = []  # 歷史數據列表（最多保留 100 筆）
latest_data = {}  # 最新一筆數據
mqtt_connected = False  # MQTT 連線狀態
```

**邏輯說明**：
- 建立 Flask 應用程式實例
- 初始化 Socket.IO 用於 WebSocket 通訊
- 設定 MQTT 連線參數
- 初始化全域變數用於數據儲存

#### 1.2 載入歷史數據（第 151-152 行）

```python
print("📂 載入歷史數據...")
load_from_csv()
```

**邏輯說明**：
- 應用程式啟動時自動從 `sensor_data.csv` 載入歷史數據
- 只保留最近 100 筆數據在記憶體中
- 如果檔案不存在或讀取失敗，會顯示警告但不會中斷啟動

#### 1.3 MQTT 客戶端啟動（第 137-156 行）

```python
# 建立 MQTT 客戶端
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# 在背景執行緒中啟動 MQTT
mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()
```

**邏輯說明**：
- 建立 MQTT 客戶端並設定回調函數
- 在背景執行緒中啟動 MQTT 連線（避免阻塞主程式）
- 使用 daemon 執行緒，主程式結束時自動終止

---

### 2. MQTT 數據接收流程

#### 2.1 連線回調（`on_connect` 函數，第 78-88 行）

```python
def on_connect(client, userdata, flags, reason_code, properties):
    global mqtt_connected
    if reason_code.is_failure:
        print(f"❌ MQTT 連線失敗: {reason_code}")
        mqtt_connected = False
    else:
        print(f"✅ MQTT 連線成功")
        mqtt_connected = True
        client.subscribe(MQTT_TOPIC, qos=1)
        print(f"✅ 已訂閱主題: {MQTT_TOPIC}")
```

**邏輯說明**：
- 當 MQTT 連線成功時，自動訂閱主題 `客廳/感測器`
- 設定 QoS=1（至少一次傳遞）
- 更新全域變數 `mqtt_connected` 狀態

#### 2.2 訊息接收處理（`on_message` 函數，第 90-135 行）

**完整處理流程**：

1. **接收原始訊息**（第 95 行）
   ```python
   payload = message.payload.decode('utf-8')
   ```

2. **解析 JSON 數據**（第 99 行）
   ```python
   data_dict = json.loads(payload)
   ```

3. **提取數據欄位**（第 102-105 行）
   ```python
   timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   temperature = data_dict.get('temperature', data_dict.get('temp', 0))
   humidity = data_dict.get('humidity', data_dict.get('humi', 0))
   light_status = data_dict.get('light_status', data_dict.get('light', '未知'))
   ```
   
   **支援的欄位名稱**：
   - 溫度：`temperature` 或 `temp`
   - 濕度：`humidity` 或 `humi`
   - 電燈：`light_status` 或 `light`

4. **更新最新數據**（第 108-113 行）
   ```python
   latest_data = {
       'light_status': light_status,
       'temperature': temperature,
       'humidity': humidity,
       'timestamp': timestamp
   }
   ```

5. **儲存到記憶體列表**（第 116-120 行）
   ```python
   sensor_data.append(latest_data.copy())
   # 只保留最近 100 筆
   if len(sensor_data) > 100:
       sensor_data.pop(0)
   ```

6. **儲存到 CSV 檔案**（第 122-129 行）
   ```python
   csv_data = {
       '時間戳記': timestamp,
       '電燈狀態': light_status,
       '溫度': temperature,
       '濕度': humidity
   }
   save_to_csv(csv_data)
   ```

7. **透過 WebSocket 推送到前端**（第 132 行）
   ```python
   socketio.emit('new_data', latest_data)
   ```

**錯誤處理**：
- 如果 JSON 解析失敗或處理過程出錯，會捕獲異常並印出錯誤訊息，但不會中斷程式執行

---

### 3. 數據儲存邏輯

#### 3.1 CSV 檔案讀取（`load_from_csv` 函數，第 36-63 行）

```python
def load_from_csv():
    global sensor_data
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                loaded_data = []
                for row in reader:
                    data_dict = {
                        'timestamp': row['時間戳記'],
                        'light_status': row['電燈狀態'],
                        'temperature': float(row['溫度']),
                        'humidity': float(row['濕度'])
                    }
                    loaded_data.append(data_dict)
                
                # 只保留最近 100 筆
                sensor_data = loaded_data[-100:]
                
                # 更新最新數據
                if sensor_data:
                    global latest_data
                    latest_data = sensor_data[-1].copy()
```

**邏輯說明**：
- 檢查 CSV 檔案是否存在
- 讀取所有歷史數據
- 只保留最近 100 筆在記憶體中
- 更新 `latest_data` 為最後一筆數據

#### 3.2 CSV 檔案寫入（`save_to_csv` 函數，第 65-76 行）

```python
def save_to_csv(data):
    file_exists = os.path.exists(CSV_FILE)
    
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['時間戳記', '電燈狀態', '溫度', '濕度']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data)
```

**邏輯說明**：
- 使用追加模式（`'a'`）寫入檔案
- 如果檔案不存在，先寫入標題列
- 每次收到新數據時自動追加一行

---

### 4. Web API 端點

#### 4.1 主頁路由（第 158-161 行）

```python
@app.route('/')
def index():
    """主頁"""
    return render_template('index.html')
```

**功能**：返回前端 HTML 頁面

#### 4.2 最新數據 API（第 163-170 行）

```python
@app.route('/api/latest')
def get_latest():
    """取得最新數據 API"""
    return jsonify({
        **latest_data,
        'mqtt_connected': mqtt_connected,
        'total_records': len(sensor_data)
    })
```

**功能**：返回最新一筆數據、MQTT 連線狀態、總記錄數

#### 4.3 歷史數據 API（第 172-175 行）

```python
@app.route('/api/history')
def get_history():
    """取得歷史數據 API"""
    return jsonify(sensor_data)
```

**功能**：返回所有歷史數據（最多 100 筆）

---

### 5. 前端邏輯流程（`templates/index.html`）

#### 5.1 初始化階段

1. **建立 Socket.IO 連線**（第 196 行）
   ```javascript
   const socket = io();
   ```

2. **初始化 Chart.js 圖表**（第 199-251 行）
   - 建立雙 Y 軸折線圖
   - 左側 Y 軸：溫度（紅色）
   - 右側 Y 軸：濕度（藍色）

3. **載入初始數據**（第 326-327 行）
   ```javascript
   fetchLatest();   // 取得最新數據
   fetchHistory();  // 取得歷史數據
   ```

#### 5.2 即時更新機制

1. **監聽 WebSocket 事件**（第 300-303 行）
   ```javascript
   socket.on('new_data', function(data) {
       console.log('收到新數據:', data);
       fetchLatest();
   });
   ```

2. **定期更新圖表**（第 330 行）
   ```javascript
   setInterval(fetchHistory, 5000);  // 每 5 秒更新一次
   ```

3. **更新顯示函數**（第 254-285 行）
   - 更新電燈狀態視覺化
   - 更新溫濕度數值
   - 更新時間戳記
   - 更新 MQTT 連線狀態指示燈
   - 更新總記錄數

---

## ✏️ 可手動修改的部分

### 1. MQTT 連線設定（`app_flask.py` 第 18-21 行）

```python
# MQTT 設定
MQTT_BROKER = "localhost"      # 可改為其他 IP 地址
MQTT_PORT = 1883                # 可改為其他埠號
MQTT_TOPIC = "客廳/感測器"      # 可改為其他主題名稱
```

**修改建議**：
- 如果 MQTT Broker 不在本機，修改 `MQTT_BROKER` 為實際 IP 地址
- 如果使用非標準埠號，修改 `MQTT_PORT`
- 如果需要監控其他主題，修改 `MQTT_TOPIC`

---

### 2. 數據保留數量（`app_flask.py` 第 54、119 行）

```python
# 第 54 行：載入時只保留最近 100 筆
sensor_data = loaded_data[-100:]

# 第 119 行：超過 100 筆時移除最舊的
if len(sensor_data) > 100:
    sensor_data.pop(0)
```

**修改建議**：
- 如果需要保留更多歷史數據，將 `100` 改為更大的數字（例如 `500`）
- 注意：保留更多數據會增加記憶體佔用

---

### 3. CSV 檔案路徑（`app_flask.py` 第 34 行）

```python
CSV_FILE = 'sensor_data.csv'
```

**修改建議**：
- 可以改為絕對路徑或相對路徑
- 例如：`CSV_FILE = '/home/pi/data/sensor_data.csv'`

---

### 4. Web 服務埠號（`app_flask.py` 第 187 行）

```python
socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
```

**修改建議**：
- 將 `port=8080` 改為其他埠號（例如 `5000`、`3000`）
- 如果只允許本機訪問，將 `host='0.0.0.0'` 改為 `host='127.0.0.1'`
- 開發時可將 `debug=False` 改為 `debug=True` 以啟用除錯模式

---

### 5. 前端更新頻率（`templates/index.html` 第 330 行）

```javascript
setInterval(fetchHistory, 5000);  // 每 5 秒更新一次
```

**修改建議**：
- 將 `5000`（毫秒）改為其他值
- 例如：`3000`（3 秒）、`10000`（10 秒）
- 注意：更新太頻繁可能增加伺服器負載

---

### 6. 前端圖表設定（`templates/index.html` 第 200-251 行）

**可修改項目**：

- **圖表顏色**（第 208、215 行）
  ```javascript
  borderColor: '#ef4444',  // 溫度線顏色（紅色）
  borderColor: '#3b82f6',  // 濕度線顏色（藍色）
  ```

- **圖表標題**（第 206、213 行）
  ```javascript
  label: '溫度 (°C)',
  label: '濕度 (%)',
  ```

- **Y 軸標題**（第 234、243 行）
  ```javascript
  text: '溫度 (°C)'
  text: '濕度 (%)'
  ```

---

### 7. 前端樣式設定（`templates/index.html` 第 9-150 行）

**可修改項目**：

- **背景漸層色**（第 18 行）
  ```css
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  ```

- **卡片顏色**（第 72 行）
  ```css
  background: white;
  ```

- **電燈狀態顏色**（第 116、121 行）
  ```css
  /* 開燈：黃色漸層 */
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  
  /* 關燈：灰色漸層 */
  background: linear-gradient(135deg, #333 0%, #555 100%);
  ```

---

### 8. 測試數據生成設定（`generate_test_data.py`）

#### 8.1 數據筆數（第 123 行）

```python
data = generate_test_data(count=50)
```

**修改建議**：改為其他數量（例如 `100`、`200`）

#### 8.2 數據範圍（第 32-33 行）

```python
base_temp = 25.0  # 基礎溫度
base_humi = 60.0  # 基礎濕度
```

**修改建議**：調整為實際環境的溫濕度範圍

#### 8.3 時間間隔（第 37 行）

```python
timestamp = base_time + timedelta(minutes=i * 5)  # 每 5 分鐘一筆
```

**修改建議**：改為其他間隔（例如 `timedelta(minutes=i * 10)` 為每 10 分鐘）

---

### 9. MQTT 測試發布設定（`test_mqtt_publish.py`）

#### 9.1 MQTT Broker 設定（第 13-15 行）

```python
BROKER = "localhost"
PORT = 1883
TOPIC = "客廳/感測器"
```

**修改建議**：與 `app_flask.py` 中的設定保持一致

#### 9.2 發布參數（第 82 行）

```python
publish_test_data(client, count=10, interval=2)
```

**修改建議**：
- `count=10`：發布的數據筆數
- `interval=2`：每筆數據間隔時間（秒）

#### 9.3 數據範圍（第 40-41 行）

```python
"temperature": round(20 + random.uniform(-5, 10), 2),  # 15-30度
"humidity": round(50 + random.uniform(-10, 20), 2),     # 40-70%
```

**修改建議**：調整為實際測試需要的數值範圍

---

### 10. 啟動腳本設定（`start.sh`）

#### 10.1 顯示的 IP 地址（第 24 行）

```bash
echo "   - http://172.20.10.3:8080"
```

**修改建議**：改為實際的 Raspberry Pi IP 地址

---

## 🔍 程式邏輯重點總結

### 數據流向

```
MQTT Broker
    ↓
on_message() 接收
    ↓
解析 JSON → 更新 latest_data → 儲存到 sensor_data[] → 寫入 CSV
    ↓
socketio.emit('new_data') 推送
    ↓
前端 WebSocket 接收
    ↓
更新顯示 + 更新圖表
```

### 關鍵設計決策

1. **記憶體管理**：只保留最近 100 筆數據，避免記憶體無限增長
2. **非阻塞設計**：MQTT 在背景執行緒運行，不影響 Web 服務
3. **即時推送**：使用 WebSocket 推送新數據，無需前端輪詢
4. **容錯處理**：JSON 解析失敗不會中斷程式，只會印出錯誤
5. **數據持久化**：每次收到數據立即寫入 CSV，確保數據不遺失

---

## 📝 修改建議與注意事項

### 修改前注意事項

1. **備份原始檔案**：修改前建議先備份
2. **測試修改**：每次修改後測試功能是否正常
3. **檢查依賴**：修改埠號或路徑時，確認相關設定一致
4. **記憶體考量**：增加數據保留數量時，注意記憶體使用情況

### 常見修改場景

1. **更換 MQTT Broker**：修改 `MQTT_BROKER` 和 `MQTT_PORT`
2. **監控多個主題**：需要修改程式邏輯，目前只支援單一主題
3. **增加數據欄位**：需要修改 CSV 欄位、前端顯示、圖表設定
4. **改變數據儲存格式**：目前只支援 CSV，如需 Excel 自動儲存需修改程式

---

## 🎯 總結

Lesson6 專案採用清晰的模組化設計，主要邏輯集中在 `app_flask.py`，前端介面在 `templates/index.html`。程式邏輯簡單易懂，大部分設定都可以透過修改常數來調整，適合學習和客製化。

**核心特點**：
- ✅ 即時數據監控
- ✅ 自動數據儲存
- ✅ WebSocket 即時推送
- ✅ 歷史數據視覺化
- ✅ 易於修改和擴充

