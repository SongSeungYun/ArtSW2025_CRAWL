import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup
from googletrans import Translator

URL = "https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api"
CSS_SELECTOR = "div.prose.prose-blue.article-content.text-prose"

def crawl():

    translator = Translator()

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
    
    html = ""
    try:
        # 최대 20초 동안 반복 시도
        for _ in range(10):
            try:
                content_div = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, CSS_SELECTOR))
                )
                html = content_div.get_attribute("innerHTML")
                if html:
                    break
            except StaleElementReferenceException:
                time.sleep(1)
    finally:
        driver.quit()

    # --- BeautifulSoup으로 파싱 ---
    soup = BeautifulSoup(html, "html.parser")

    result = []
    # 모든 h2 찾기
    for h2 in soup.find_all("h2"):
        # h2 제목 먼저 저장
        result.append(f"=== {h2.get_text(strip=True)} ===")

        # h2 이후의 형제 태그들을 탐색
        for sibling in h2.find_next_siblings():
            if sibling.name in ["h2", "h1"]:  # 다음 h2나 h1이 나오면 중단
                break
            if sibling.name in ["p","pre"]:  # p 태그만 수집
                result.append(sibling.get_text(strip=True))

        # 구분을 위해 줄바꿈 추가
        result.append("")

    return str(translator.translate("\n".join(result), src='en', dest='ko'))


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