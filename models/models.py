from sqlalchemy.orm import (
    declarative_base, relationship
)
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, TIMESTAMP, text
)
# SQLAlchemy Base
Base = declarative_base()

# ORM 모델 정의
class Place(Base):
    __tablename__ = "place"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    address = Column(String(255), nullable=False)
    business_hours = Column(String(255), nullable=True)
    hours = relationship("PlaceHours", back_populates="place", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="place", cascade="all, delete-orphan")
    blogs = relationship("Blog", back_populates="place", cascade="all, delete-orphan")
    photos = relationship("PlacePhoto", back_populates="place", cascade="all, delete-orphan")
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True)

class PlaceHours(Base):
    __tablename__ = "place_hours"
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(Integer, ForeignKey("place.id"), nullable=False)
    day = Column(String(10), nullable=False)
    time = Column(String(50), nullable=False)
    place = relationship("Place", back_populates="hours")
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True)

class Review(Base):
    __tablename__ = "review"
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(Integer, ForeignKey("place.id"), nullable=False)
    author = Column(String(100), nullable=False)
    review_date = Column(String(100), nullable=True)
    visit_count = Column(String(20), nullable=True)
    profile_review = Column(Integer, nullable=True)
    profile_photo = Column(Integer, nullable=True)
    profile_follower = Column(Integer, nullable=True)
    follow = Column(Boolean, nullable=True)
    visit_info = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    tags = Column(String(255), nullable=True)  # 콤마구분
    review_more = Column(Boolean, nullable=True)
    extra_review_line = Column(String(255), nullable=True)
    receipt = Column(String(50), nullable=True)
    place = relationship("Place", back_populates="reviews")
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True)

class Blog(Base):
    __tablename__ = "blog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(Integer, ForeignKey("place.id"), nullable=False)
    title = Column(String(255), nullable=False)
    author = Column(String(100), nullable=True)
    date = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    blog_url = Column(String(255), nullable=True)
    images = relationship("BlogImage", back_populates="blog", cascade="all, delete-orphan")
    place = relationship("Place", back_populates="blogs")
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True)

class BlogImage(Base):
    __tablename__ = "blog_image"
    id = Column(Integer, primary_key=True, autoincrement=True)
    blog_id = Column(Integer, ForeignKey("blog.id"), nullable=False)
    image_url = Column(String(255), nullable=False)
    blog = relationship("Blog", back_populates="images")
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True)

class PlacePhoto(Base):
    __tablename__ = "place_photo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(Integer, ForeignKey("place.id"), nullable=False)
    image_url = Column(String(255), nullable=False)
    place = relationship("Place", back_populates="photos")
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=True)