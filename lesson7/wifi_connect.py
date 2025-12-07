# wifi_connect.py
# 作者：ChatGPT for 徐國堂老師
# 適用：Raspberry Pi Pico W（MicroPython）

import network
import time
import socket

# -------------------------------
# 你可以設定你的 WiFi 資訊
# -------------------------------
WIFI_SSID = "F602-kk-wifi"
WIFI_PASSWORD = "raspberry"


# -------------------------------
# WiFi 連線函式
# -------------------------------
def connect(ssid=WIFI_SSID, password=WIFI_PASSWORD, retry=20):
    """
    連線到 WiFi。
    retry = 嘗試次數（每次間隔 1 秒）
    回傳：連線後的 WLAN 物件
    """
    wlan = network.WLAN(network.STA_IF)

    if wlan.isconnected():
        print("已經連線過 WiFi：", wlan.ifconfig())
        return wlan

    print("啟動 WLAN...")
    wlan.active(True)
    time.sleep(1)

    print(f"準備連線 SSID：{ssid}")
    wlan.connect(ssid, password)

    for i in range(retry):
        status = wlan.status()
        if wlan.isconnected():
            print("WiFi 連線成功！")
            print("IP 資訊：", wlan.ifconfig())
            return wlan

        # 顯示連線狀態碼（幫助診斷問題）
        status_msg = {
            1000: "IDLE - 閒置",
            1001: "CONNECTING - 連線中",
            1010: "GOT_IP - 已取得 IP",
            202: "WRONG_PASSWORD - 密碼錯誤",
            201: "NO_AP_FOUND - 找不到此 SSID",
            200: "AUTH_FAIL - 認證失敗",
            204: "ASSOC_FAIL - 關聯失敗",
            205: "HANDSHAKE_TIMEOUT - 握手逾時"
        }
        status_text = status_msg.get(status, f"未知狀態碼: {status}")
        print(f"連線中... ({i+1}/{retry}) [狀態: {status_text}]")
        time.sleep(1)

    # 連線失敗，顯示詳細錯誤資訊
    final_status = wlan.status()
    error_msg = f"❌ WiFi 連線失敗（狀態碼: {final_status}）\n"
    error_msg += f"   嘗試連線的 SSID: {ssid}\n"
    
    if final_status == 201:
        error_msg += "   可能原因：找不到此 WiFi 網路（SSID 不正確或訊號太弱）"
    elif final_status == 202:
        error_msg += "   可能原因：WiFi 密碼錯誤"
    elif final_status == 204:
        error_msg += "   可能原因：無法與路由器建立關聯（訊號太弱或路由器拒絕）"
    elif final_status == 205:
        error_msg += "   可能原因：連線握手逾時（訊號不穩定）"
    else:
        error_msg += "   可能原因：請檢查 SSID/密碼、訊號強度或距離"
    
    raise RuntimeError(error_msg)

# -------------------------------
# 斷線函式
# -------------------------------
def disconnect():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        wlan.disconnect()
        wlan.active(False)
        print("已斷線")
    else:
        print("目前沒有 WiFi 連線")

# -------------------------------
# 是否連線成功？
# -------------------------------
def is_connected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.isconnected()

# -------------------------------
# 取得 IP 位址
# -------------------------------
def get_ip():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    return None

# -------------------------------
# 測試連線到外部網站（例如 Google）
# -------------------------------
def test_internet(host="8.8.8.8", port=53, timeout=3):
    """
    使用 UDP 測試外部網路是否可連線
    """
    try:
        addr = socket.getaddrinfo(host, port)[0][-1]
        s = socket.socket()
        s.settimeout(timeout)
        s.connect(addr)
        s.close()
        return True
    except:
        return False