import argparse
import asyncio
import random
from playwright.async_api import async_playwright
import time
import os
import aiohttp
import aiofiles
from models.db_manager import DBManager
from models.DTOs import HomeDataDTO, ReviewDataDTO, BlogDataDTO, PhotoDataDTO
from utils.logger import Logger
logger = Logger()

BLOG_SAVE_DIR = "BLOG_IMG_DOWNLOAD"

TAB_PHOTO_SAVE_DIR = "TAB_PHOTO_IMG_DOWNLOAD"


class NaverMapMetaCrawler:
    def __init__(self, headless=True, db_manager: DBManager = None):
        self.headless = headless
        self.db_manager: DBManager = db_manager

    async def download_random_images(self, image_list, download_path=BLOG_SAVE_DIR):
        try:
            os.makedirs(download_path, exist_ok=True)
            selected_images = random.sample(image_list, 2)
            async with aiohttp.ClientSession() as session:
                for idx, image_url in enumerate(selected_images):
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            file_path = os.path.join(download_path, f"random_image_{idx + 1}.jpg")
                            async with aiofiles.open(file_path, "wb") as f:
                                await f.write(await resp.read())
                            logger.info(f"Image Downloaded Successfully: {file_path}")
                        else:
                            logger.info(f"Image Download Failed: {image_url}")
        except Exception as e:
            logger.error(f"Image Download Failed: {str(e)}")

    async def crawl(self, store_name):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                locale="ko-KR",
                timezone_id="Asia/Seoul"
            )
            page = await context.new_page()
            await page.goto("https://map.naver.com/v5/")
            await page.wait_for_timeout(2000)

            # 검색
            input_box = await page.query_selector("div.input_box input")
            if input_box is None:
                await page.click("div.input_box")
                await page.wait_for_selector("div.input_box input", timeout=5000)
                input_box = await page.query_selector("div.input_box input")

            await input_box.fill(store_name)
            await input_box.press("Enter")
            await page.wait_for_timeout(5000)

            # 상세 프레임 접근
            await page.wait_for_selector("iframe#entryIframe", timeout=10000)
            # 2. entryIframe 객체 얻기
            entry_iframe = await page.query_selector("iframe#entryIframe")
            entry = await entry_iframe.content_frame()

            home_data_raw = await self.fetch_home(entry, store_name)
            home_data = HomeDataDTO(**home_data_raw)
            review_data_raw = await self.fetch_reviews(entry)
            review_data = ReviewDataDTO(**review_data_raw)
            blog_data_raw = await self.fetch_blog(entry)
            blog_data = BlogDataDTO(**blog_data_raw)
            photo_data_raw = await self.fetch_photos(entry)
            photo_data = PhotoDataDTO(**photo_data_raw)


            # self.db_manager.add_place_with_all(home_data, review_data, blog_data, photo_data)

            result = {
                "home_data": home_data,
                "review_data": review_data,
                "blog_data": blog_data,
                "photo_data": photo_data
            }

            await self.db_manager.add_place_with_all(home_data, review_data, blog_data, photo_data)

            await browser.close()
            return result

    async def fetch_home(self, entry, name):
        # 2. 도로명 주소 span 찾기
        await entry.wait_for_selector("span.LDgIH", timeout=5000)
        road_name_elem = await entry.query_selector("span.LDgIH")
        address = (await road_name_elem.text_content()).strip()

        # 3. 영업 시간 span 찾기
        await entry.wait_for_selector("span.U7pYf", timeout=5000)
        business_hours_elem = await entry.query_selector("span.U7pYf")
        business_hours = (await business_hours_elem.text_content()).strip()
        
        # 2. '펼쳐보기' 버튼 클릭 (있을 때만)
        await entry.wait_for_selector("span.place_blind", timeout=5000)
        expand_btn = await entry.query_selector("span.place_blind:text('펼쳐보기')")
        if expand_btn:
            await expand_btn.click()
            time.sleep(1)

        await entry.wait_for_selector("div.w9QyJ", timeout=5000)
        day_divs = await entry.query_selector_all("div.w9QyJ")

        hours = []
        for div in day_divs:
            # 요일 추출
            day_elem = await div.query_selector("span.A_cdD span.i8cJw")
            time_elem = await div.query_selector("div.H3ua4")
            # 시간 추출
            if day_elem and time_elem:
                day = (await day_elem.text_content()).strip()
                time_text = (await time_elem.text_content()).strip()
                hours.append({"day": day, "time": time_text})

        home_data = {
            "name": name,
            "address": address,
            "business_hours": business_hours,
            "hours": hours
        }

        return home_data

    async def fetch_reviews(self, entry):
        # 리뷰 탭 클릭
        taps = await entry.query_selector_all("div.YYh8o.gHymq a")
        for tap in taps:
            if (await tap.text_content()).strip() == "리뷰":
                await tap.click()
                break
        await entry.wait_for_timeout(2000)

        review_elements = await entry.query_selector_all("#_review_list li")
        reviews = []
        for r in review_elements[:4]:  # 상위 4개만
            text = (await r.inner_text())
            reviews.append(text.strip())

        parsed_review_list = []
        for review in reviews:
            parsed_review = await parse_review_text(review)
            parsed_review_list.append(parsed_review)
        

        review_data = {
            "reviews": parsed_review_list
        }

        return review_data

    async def fetch_blog(self, entry):
        # 블로그 리뷰 탭 클릭
        taps = await entry.query_selector_all("div.YYh8o.gHymq a")
        for tap in taps:
            if (await tap.text_content()).strip() == "리뷰":
                await tap.click()
                break
        await entry.wait_for_timeout(2000)

        reviews_tap = await entry.query_selector_all("div.GWcCA a")
        for reviews_tap in reviews_tap:
            if (await reviews_tap.text_content()).strip() == "블로그 리뷰":
                await reviews_tap.click()
                break
        await entry.wait_for_timeout(2000)

        # 블로그 첫 번째 링크 가져오기
        first_blog = await entry.query_selector("ul li.EblIP a")
        blog_url = await first_blog.get_attribute("href")

        blog_data = await self.fetch_blog_contents(blog_url, entry)
        blog_data.update({"blog_url": blog_url})
        
        return blog_data

    async def fetch_blog_contents(self, url, entry):
        page = await entry.page.context.new_page()
        await page.goto(url)
        await page.wait_for_timeout(3000)  # 페이지 로딩 대기

        # blog_frame = await page.frame_locator("iframe#mainFrame").first
        frame_locator =page.frame_locator("iframe#mainFrame")
        blog_frame = frame_locator.first

        title = blog_frame.locator(".se-module.se-module-text.se-title-text").first
        blog_title = (await title.text_content()).strip()

        author = blog_frame.locator(".link.pcol2").first
        nickname = (await author.text_content()).strip()

        date = blog_frame.locator(".se_publishDate.pcol2").first
        datetime = (await date.text_content()).strip()

        contents = await blog_frame.locator(".se-component.se-text.se-l-default").all()
        sum_contents = ""
        for content in contents:
            clean_content = (await content.text_content()).replace("\u200b", "").strip()
            sum_contents += clean_content


        image_elements = await blog_frame.locator("div.se-component.se-image.se-l-default.__se-component img").all()
        image_list = []
        
        for element in image_elements:
            src = await element.get_attribute("data-lazy-src")
            if src:
                image_list.append(src)

        await self.download_random_images(image_list, BLOG_SAVE_DIR) # 랜덤으로 2개 찍어서 로컬에 다운로드.
        
        blog_data = {
            "title": blog_title,
            "author": nickname,
            "date": datetime,
            "content": sum_contents,
            "images": image_list
        }

        return blog_data

    async def fetch_photos(self, entry):
        # 사진 탭 클릭
        taps = await entry.query_selector_all("div.YYh8o.gHymq a")
        for tap in taps:
            if (await tap.text_content()).strip() == "사진":
                await tap.click()
                break
        await entry.wait_for_timeout(2000)
        try:
            # 다운로드 폴더 생성
            os.makedirs(TAB_PHOTO_SAVE_DIR, exist_ok=True)
            
            large_images = []
            has_more_images = True
            
            while has_more_images:
                # 이미지 요소 선택
                image_elements = entry.locator("div.Nd2nM div.wzrbN img")
                
                for i in range(await image_elements.count()):
                    element = image_elements.nth(i)
                    src = (await element.get_attribute("src"))
                    if src:
                        intrinsic_width = (await element.evaluate("(img) => img.naturalWidth"))
                        intrinsic_height = (await element.evaluate("(img) => img.naturalHeight"))
                        if intrinsic_width >= 300 and intrinsic_height >= 300:
                            large_images.append(src)

                        # large_images.append(src)
                
                # 만약 큰 이미지가 없다면 스크롤
                if not large_images or len(large_images) < 3:
                    (await entry.evaluate("window.scrollBy(0, window.innerHeight)"))
                    await entry.wait_for_timeout(2000)  # 스크롤 후 대기
                else:
                    has_more_images = False
        
                # 이미지 다운로드
                async with aiohttp.ClientSession() as session:
                    for idx, image_url in enumerate(large_images[:3]):
                        async with session.get(image_url) as response:
                            if response.status == 200:
                                file_path = os.path.join(TAB_PHOTO_SAVE_DIR, f"tab_photo_image_{idx + 1}.jpg")
                                async with aiofiles.open(file_path, "wb") as f:
                                    await f.write(await response.read())
                                logger.info(f"Image Downloaded Successfully: {file_path}")
                            else:
                                logger.error(f"Image Download Failed: {image_url}")

            photo_data = {
                "images": large_images[:3]
            }


            return photo_data
        
        except Exception as e:
            logger.error(f"Image Processing Failed: {str(e)}")

        pass

async def parse_review_text(review_text: str) -> dict:
    """
    네이버 리뷰 원본 텍스트를 의미별로 파싱해 딕셔너리로 반환합니다.
    """
    import re
    lines = [line for line in review_text.split('\n') if line.strip()]

    # 1. 작성자
    author = lines[0] if len(lines) > 0 else None

    # 2. 프로필 정보
    profile_match = re.search(r'리뷰 (\d+)사진 (\d+)팔로워 (\d+)', lines[1]) if len(lines) > 1 else None
    profile = {
        "review": int(profile_match.group(1)) if profile_match else None,
        "photo": int(profile_match.group(2)) if profile_match else None,
        "follower": int(profile_match.group(3)) if profile_match else None,
    }

    # 3. 팔로우 여부
    follow = any("follow" in l for l in lines[:4])

    # 4. 방문정보
    visit_info = None
    for l in lines[2:6]:
        if any(x in l for x in ["방문", "예약", "대기", "입장", "일상", "지인", "동료"]):
            visit_info = l
            break

    # 5. 본문(리뷰 내용)
    body_lines = []
    for line in lines[4:]:
        if "더보기" in line:
            break
        body_lines.append(line)
    body = " ".join(body_lines)

    # 6. 태그
    tag_line = next((l for l in lines if "+" in l or "음식이 맛있어요" in l), None)
    tags = []
    if tag_line:
        tags = re.findall(r"[가-힣A-Za-z0-9\s]+", tag_line)
        tags = [t.strip() for t in tags if t.strip() and t.strip() != "+4"]

    # 7. 추가 리뷰 안내
    extra_review_line = next((l for l in lines if "개의 리뷰가 더 있습니다" in l), None)

    # 8. 방문일, 방문차수, 인증수단
    visit_date = next((l for l in lines if re.match(r"\d{4}년", l)), None)
    visit_count = next((l for l in lines if "번째 방문" in l), None)
    receipt = next((l for l in lines if "영수증" in l or "인증" in l), None)

    return {
        "author": author,
        "profile": profile,
        "follow": follow,
        "visit_info": visit_info,
        "body": body,
        "tags": tags,
        "review_more": any("더보기" in l for l in lines),
        "extra_review_line": extra_review_line,
        "visit_date": visit_date,
        "visit_count": visit_count,
        "receipt": receipt
    }

async def main(store_name):
    db = DBManager()
    try:
        await db.create_all_tables()
        crawler = NaverMapMetaCrawler(headless=False, db_manager=db)
        await crawler.crawl(store_name)
    finally:
        await db.aclose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naver Map Meta Crawler")
    parser.add_argument("store_name", type=str, help="Name of the store to crawl")
    args = parser.parse_args()

    asyncio.run(main(args.store_name))
