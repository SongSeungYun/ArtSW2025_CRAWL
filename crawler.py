import sys
import io
import os
import time
import psycopg2
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup
from googletrans import Translator
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
DB_CONFIG = {
    "dbname": os.getenv("DB_DATABASE"),
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

URL = "https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api"
CSS_SELECTOR = "div.prose.prose-blue.article-content.text-prose"
UPDATE_SELECTOR = "div.text-tertiary.mb-10.text-sm.tracking-wide"

def crawl():

    title, content, created_at="","",""
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
        # 1️⃣ 업데이트 날짜 먼저 가져오기
        try:
            update_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, UPDATE_SELECTOR))
            )
            updated_text = update_div.text.strip()
            print("업데이트 날짜:", updated_text)
        except Exception as e:
            print("업데이트 날짜 가져오기 실패:", e)
            return None, None, None

        # "1일 전"이 아니면 본문 가져올 필요 없음
        if "1일 전" not in updated_text:
            print("최근 1일 이내 업데이트가 아님 → 본문 수집 안 함")
            return None, None, None

        # 2️⃣ 본문 가져오기
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
    try:
        translated = translator.translate("\n".join(result), src='en', dest='ko')
    except Exception as e:
        print("번역 중 오류 발생:", e)
        return "\n".join(result)
    current_time=str(datetime.now())
    title = time_to_title(current_time)
    content = process_korean_text(translated.text)
    created_at = current_time
    return title,content,created_at

def time_to_title(current_time):
    return current_time[:4]+"년 "+current_time[5:7]+"월 "+current_time[8:10]+"일 프롬프팅 모범 사례"

def process_korean_text(text):
    text_list=text.split(" ")
    replacements = {"효과적인": "효과적인 예시", "나은": "나은 예시"}
    for i, word in enumerate(text_list):
        if word in replacements:
            text_list[i] = replacements[word]
    return " ".join(text_list)

def save_to_postgres(title, content, created_at):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO "Board"."MonthlyPrompt" (title, content, created_at)
            VALUES (%s, %s, %s)
            """,
            (title, content, created_at),
        )
        conn.commit()
        print("데이터베이스 저장 완료!")
    except Exception as e:
        print("DB 저장 중 오류:", e)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    title, content, created_at = crawl()
    if title and content and created_at:
        save_to_postgres(title, content, created_at)