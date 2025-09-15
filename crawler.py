import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

URL = "https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api"
CSS_SELECTOR = "div.prose.prose-blue.article-content.text-prose"

def crawl():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    
    content_text = ""
    try:
        # 최대 20초 동안 반복 시도
        for _ in range(10):
            try:
                content_div = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, CSS_SELECTOR))
                )
                content_text = content_div.get_attribute("innerText")
                if content_text:
                    break
            except StaleElementReferenceException:
                # 요소가 사라졌다면 잠시 대기 후 재시도
                time.sleep(1)
    finally:
        driver.quit()

    return content_text

def save_to_file(content):
    if content:
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print("크롤링 + 파일 저장 완료! 본문 길이:", len(content))
    else:
        print("본문이 없어서 저장하지 않음")

if __name__ == "__main__":
    content = crawl()
    save_to_file(content)
