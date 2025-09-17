from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import (
    sessionmaker, scoped_session
)
from contextlib import contextmanager
from models.models import (
    Base, Place, PlaceHours, Review, Blog, BlogImage, PlacePhoto
)
from configs.config import Configs
from configs.config_model import MySQLConfig
import aiomysql
from models.DTOs import HomeDataDTO, ReviewDTO, ReviewDataDTO, BlogDataDTO, PhotoDataDTO

CONFIG_PATH = "configs/config.toml"
config = Configs(CONFIG_PATH)
db_config = config.get(MySQLConfig)

# 환경변수 또는 config에서 DB 접속 정보 읽기
DATABASE_URL = f"mysql+aiomysql://{db_config.user}:{db_config.pw}@{db_config.host}:{db_config.port}/{db_config.db}?charset=utf8mb4"

# 엔진/세션/풀 최적화
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
    future=True
)
sessionFactory = sessionmaker(bind=async_engine, class_=AsyncSession, autoflush=False, autocommit=False, expire_on_commit=False)
Session = scoped_session(sessionFactory)

# 트랜잭션/세션 관리 컨텍스트
@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

# CRUD 및 트랜잭션 예시
class DBManager:
    def __init__(self):
        self.engine = async_engine
        self.session = Session

    async def create_database_if_not_exists(self):
        pool = await aiomysql.create_pool(
            host=db_config.host,
            user=db_config.user,
            password=db_config.pw,
            charset='utf8mb4',
            autocommit=True,
            minsize=1,
            maxsize=1,
        )

        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"CREATE DATABASE IF NOT EXISTS {db_config.db} "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                    )
        finally:
            pool.close()
            await pool.wait_closed()

    async def create_all_tables(self):
        await self.create_database_if_not_exists()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def aclose(self):
        await self.engine.dispose()

    async def add_place_with_all(self, place_data: HomeDataDTO, reviews_list: ReviewDataDTO, blog_data: BlogDataDTO, photo_list: PhotoDataDTO):
        async with self.session() as session:
            try:
                # Place 데이터 저장
                place = Place(
                    name=place_data.name,
                    address=place_data.address,
                    business_hours=place_data.business_hours
                )
                session.add(place)
                await session.flush()  # place.id 확보

                # PlaceHours 데이터 저장
                for h in place_data.hours:
                    session.add(PlaceHours(place_id=place.id, **h.model_dump()))

                # Review 데이터 저장
                for r in reviews_list.reviews:
                    review_data: ReviewDTO = r
                    review = Review(
                        place_id=place.id,
                        author=review_data.author,
                        review_date=review_data.visit_date,
                        visit_count=review_data.visit_count,
                        profile_review=review_data.profile.review,
                        profile_photo=review_data.profile.photo,
                        profile_follower=review_data.profile.follower,
                        follow=review_data.follow,
                        visit_info=review_data.visit_info,
                        body=review_data.body,
                        tags=','.join(review_data.tags),
                        review_more=review_data.review_more,
                        extra_review_line=review_data.extra_review_line,
                        receipt=review_data.receipt
                    )
                    session.add(review)

                # Blog 데이터 저장
                if blog_data:
                    date_str = blog_data.date
                    date_obj = datetime.strptime(date_str, "%Y. %m. %d. %H:%M")
                    blog = Blog(
                        place_id=place.id,
                        title=blog_data.title,
                        author=blog_data.author,
                        date=date_obj,
                        content=blog_data.content,
                        blog_url=blog_data.blog_url
                    )
                    session.add(blog)
                    await session.flush()

                    # BlogImage 데이터 저장
                    for img_url in blog_data.images:
                        session.add(BlogImage(blog_id=blog.id, image_url=img_url))

                # PlacePhoto 데이터 저장
                for img_url in photo_list.images:
                    session.add(PlacePhoto(place_id=place.id, image_url=img_url))
                    
                # 트랜잭션 커밋
                await session.commit()
            except Exception as e:
                # 롤백은 session_scope에서 자동 처리
                raise

    # 예시: 단일 Place 조회
    async def get_place_by_id(self, place_id):
        async with session_scope() as session:
            return session.query(Place).filter_by(id=place_id).first()

    # 예시: 전체 Place 리스트
    async def get_all_places(self):
        async with session_scope() as session:
            return session.query(Place).all()

