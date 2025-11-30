from machine import Timer,Pin
import time

led = Pin("LED", mode=Pin.OUT)
flash_count = 0  # 追蹤當前閃爍次數
flash_timer = None  # 用於快速閃爍的 Timer

def flash_callback(n):
    """快速閃爍的回調函數，用於實現閃兩次"""
    global flash_count, flash_timer, led
    
    if flash_count < 3:
        # 切換 LED 狀態
        if led.value() == 0:
            led.on()
        else:
            led.off()
        flash_count += 1
    else:
        # 已經閃了兩次，停止快速閃爍 Timer
        flash_timer.deinit()
        flash_timer = None
        flash_count = 0
        led.off()  # 確保最後是關閉狀態

def callback2000(n):    
    """每五秒觸發一次，啟動快速閃兩次"""
    global flash_count, flash_timer
    
    # 重置計數器並啟動快速閃爍
    flash_count = 0
    # 使用較快的 Timer（每 200 毫秒）來實現快速閃兩次
    flash_timer = Timer(period=100, callback=flash_callback)
    
def main():
    # period=5000 表示每 5000 毫秒（5 秒）觸發一次
    # 每次觸發時會快速閃兩次
    timer = Timer(period=5000, callback=callback2000)
    
if __name__ == "__main__":
    main()