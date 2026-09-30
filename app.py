import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def solve_turnstile(driver, timeout=30):
    """
    处理 Turnstile 验证：
    1. 寻找 Turnstile iframe 并切入
    2. 点击 Checkbox 复选框
    3. 等待转圈结束并直接判断 Checkbox 是否变为已打勾状态 (aria-checked="true")
    """
    print("⏳ 开始检测 Turnstile 验证框...")
    
    # 1. 尝试定位并切换到 Turnstile iframe
    turnstile_iframe = None
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        try:
            # 常见 Turnstile iframe 匹配
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='challenges.cloudflare.com']")
            if iframes:
                turnstile_iframe = iframes[0]
                break
        except Exception:
            pass
        time.sleep(1)

    if not turnstile_iframe:
        print("⚠️ 未找到 Turnstile iframe，可能页面不需要验证或加载慢。")
        return True  # 如果没找到，可能页面不需要验证，直接返回

    # 2. 切换进入 iframe
    driver.switch_to.frame(turnstile_iframe)
    print("✅ 已成功切换至 Turnstile iframe")

    # 3. 寻找并点击 Checkbox
    try:
        # Turnstile 复选框通常是 input[type='checkbox'] 或 label / .ctp-checkbox
        checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='checkbox'], .ctp-checkbox, #challenge-stage"))
        )
        print("👆 准备点击 Turnstile 复选框...")
        checkbox.click()
        print("✅ 已点击复选框，等待 Cloudflare 转圈验证...")
        
        # 【关键增加延时】：点击后先强制等待 4 秒，让 Turnstile 充分转圈验证，避免过快连续重试
        time.sleep(4)
        
    except Exception as e:
        print(f"❌ 点击 Turnstile 复选框失败或已自动通过: {e}")

    # 4. 轮询检测 Checkbox 是否打勾 (aria-checked == "true")
    check_timeout = 20  # 点击后的最大等待时间
    check_end_time = time.time() + check_timeout
    is_success = False

    while time.time() < check_end_time:
        try:
            # 重新获取复选框或其外层容器元素
            cb_element = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'], [role='checkbox']")
            
            # 直接判断 aria-checked 属性（打勾时为 "true"）
            aria_checked = cb_element.get_attribute("aria-checked")
            
            # 有些页面打勾后父级 wrapper 元素类名会包含 'success' 或 'checked'
            class_name = cb_element.get_attribute("class") or ""
            
            if aria_checked == "true" or "success" in class_name or "checked" in class_name:
                print("🎉 检测到 Turnstile 复选框已成功打勾 (aria-checked=true)！")
                is_success = True
                break
            else:
                print("⏳ 还在转圈或验证中，等待 2 秒后再次检测...")
        except Exception as e:
            # 如果元素找不到，可能页面已自动跳转/刷新，说明验证已通过
            print("ℹ️ Checkbox 元素消失或页面跳转，默认判定为通过")
            is_success = True
            break
            
        # 【关键增加延时】：每次检测之间间隔 2 秒
        time.sleep(2)

    # 切回主文档页面
    driver.switch_to.default_content()

    if is_success:
        print("✅ Turnstile 验证通过！")
        # 切回主页面后再给予 2 秒缓冲时间，确保页面提交或刷新完成
        time.sleep(2)
        return True
    else:
        print("❌ Turnstile 验证超时未通过 (未检测到打勾状态)")
        return False


# 使用示例 / 调用逻辑
if __name__ == "__main__":
    # 假设 driver 已经初始化
    # driver = webdriver.Chrome(...)
    
    success = solve_turnstile(driver, timeout=30)
    if not success:
        # 发送 Telegram 截图通知等逻辑...
        print("发送 Telegram 截图: ❌ Turnstile 验证超时未通过")
