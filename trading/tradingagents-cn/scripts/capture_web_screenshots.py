#!/usr/bin/env python3
"""
Web界面截图捕获脚本
用于自动化捕获TradingAgents-CN Web界面的截图
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('screenshot')

def check_dependencies():
    """检查截图所需的依赖"""
    try:
        import selenium
        from selenium import webdriver
        logger.info("✅ Selenium已安装")
        return True
    except ImportError:
        logger.error("❌ 缺少Selenium依赖")
        logger.info("💡 安装命令: pip install selenium")
        return False

def check_web_service():
    """检查Web服务是否运行"""
    try:
        import requests
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Web服务正在运行")
            return True
        else:
            logger.warning(f"⚠️ Web服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 无法连接到Web服务: {e}")
        return False

def start_web_service():
    """启动Web服务"""
    logger.info("🚀 正在启动Web服务...")
    
    # 检查是否有Docker环境
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("🐳 检测到Docker环境，尝试启动Docker服务...")
            subprocess.run(["docker-compose", "up", "-d"], cwd=project_root)
            time.sleep(10)  # 等待服务启动
            return check_web_service()
    except FileNotFoundError:
        pass
    
    # 尝试本地启动
    logger.info("💻 尝试本地启动Web服务...")
    try:
        # 启动Web服务（后台运行）
        subprocess.Popen([
            sys.executable, "start_web.py"
        ], cwd=project_root)
        
        # 等待服务启动
        for i in range(30):
            time.sleep(2)
            if check_web_service():
                return True
            logger.info(f"⏳ 等待服务启动... ({i+1}/30)")
        
        logger.error("❌ Web服务启动超时")
        return False
        
    except Exception as e:
        logger.error(f"❌ 启动Web服务失败: {e}")
        return False

def capture_screenshots():
    """捕获Web界面截图"""
    if not check_dependencies():
        return False
    
    if not check_web_service():
        logger.info("🔄 Web服务未运行，尝试启动...")
        if not start_web_service():
            return False
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # 创建WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # 访问Web界面
            logger.info("🌐 正在访问Web界面...")
            driver.get("http://localhost:8501")
            
            # 等待页面加载
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待Streamlit完全加载
            time.sleep(5)
            
            # 创建截图目录
            screenshots_dir = project_root / "docs" / "images"
            screenshots_dir.mkdir(exist_ok=True)
            
            # 截图1: 主界面
            logger.info("📸 捕获主界面截图...")
            driver.save_screenshot(str(screenshots_dir / "web-interface-main.png"))
            
            # 模拟输入股票代码
            try:
                stock_input = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                stock_input.clear()
                stock_input.send_keys("AAPL")
                time.sleep(2)
            except:
                logger.warning("⚠️ 无法找到股票输入框")
            
            # 截图2: 配置界面
            logger.info("📸 捕获配置界面截图...")
            driver.save_screenshot(str(screenshots_dir / "web-interface-config.png"))
            
            # 尝试点击分析按钮（如果存在）
            try:
                analyze_button = driver.find_element(By.XPATH, "//button[contains(text(), '开始分析')]")
                analyze_button.click()
                time.sleep(3)
                
                # 截图3: 进度界面
                logger.info("📸 捕获进度界面截图...")
                driver.save_screenshot(str(screenshots_dir / "web-interface-progress.png"))
                
            except:
                logger.warning("⚠️ 无法找到分析按钮或触发分析")
            
            # 截图4: 侧边栏
            logger.info("📸 捕获侧边栏截图...")
            driver.save_screenshot(str(screenshots_dir / "web-interface-sidebar.png"))
            
            logger.info("✅ 截图捕获完成")
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"❌ 截图捕获失败: {e}")
        return False

def create_screenshot_guide():
    """创建截图指南"""
    guide_content = f"""# 📸 Web界面截图捕获指南

## 🎯 自动截图

运行自动截图脚本:
```bash
python scripts/capture_web_screenshots.py
```

## 📋 手动截图步骤

### 1. 启动Web服务
```bash
# 方法1: 本地启动
python start_web.py

# 方法2: Docker启动  
docker-compose up -d
```

### 2. 访问界面
打开浏览器访问: http://localhost:8501

### 3. 捕获截图
按照以下场景进行截图:

#### 🏠 主界面 (web-interface-main.png)
- 显示完整的分析配置表单
- 输入示例股票代码: AAPL 或 000001
- 选择标准分析深度 (3级)

#### 📊 分析进度 (web-interface-progress.png)  
- 开始分析后的进度显示
- 显示进度条和预计时间
- 显示已完成的分析步骤

#### 📈 分析结果 (web-interface-results.png)
- 完整的分析报告展示
- 投资建议和风险评估
- 导出按钮区域

#### ⚙️ 模型配置 (web-interface-models.png)
- 侧边栏的模型配置界面
- LLM提供商选择
- 快速选择按钮

## 📐 截图规范

- **分辨率**: 1920x1080 或更高
- **格式**: PNG格式
- **质量**: 高清，文字清晰
- **内容**: 完整功能区域，真实数据

## 🔧 故障排除

### Chrome驱动问题
```bash
# 安装ChromeDriver
# Windows: choco install chromedriver
# Mac: brew install chromedriver  
# Linux: apt-get install chromium-chromedriver
```

### Selenium安装
```bash
pip install selenium
```

---
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    guide_path = project_root / "docs" / "images" / "screenshot-guide.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    logger.info(f"📝 截图指南已创建: {guide_path}")

def main():
    """主函数"""
    logger.info("🚀 TradingAgents-CN Web界面截图捕获工具")
    logger.info("=" * 50)
    
    # 创建截图指南
    create_screenshot_guide()
    
    # 询问用户是否要自动捕获截图
    try:
        choice = input("\n是否要自动捕获Web界面截图? (y/n): ").lower().strip()
        if choice in ['y', 'yes', '是']:
            if capture_screenshots():
                logger.info("🎉 截图捕获成功完成!")
                logger.info("📁 截图保存位置: docs/images/")
            else:
                logger.error("❌ 截图捕获失败")
                logger.info("💡 请参考手动截图指南: docs/images/screenshot-guide.md")
        else:
            logger.info("📖 请参考手动截图指南: docs/images/screenshot-guide.md")
    except KeyboardInterrupt:
        logger.info("\n👋 用户取消操作")

if __name__ == "__main__":
    main()
