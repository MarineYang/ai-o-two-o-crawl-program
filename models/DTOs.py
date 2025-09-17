from pydantic import BaseModel
from typing import List, Optional

class PlaceHoursDTO(BaseModel):
    day: str
    time: str

class HomeDataDTO(BaseModel):
    name: str
    address: str
    business_hours: str
    hours: List[PlaceHoursDTO]

class ProfileDTO(BaseModel):
    review: Optional[int]
    photo: Optional[int]
    follower: Optional[int]

class ReviewDTO(BaseModel):
    author: str
    profile: Optional[ProfileDTO]
    follow: Optional[bool]
    visit_info: Optional[str]
    body: Optional[str]
    tags: Optional[List[str]]  
    review_more: Optional[bool]
    extra_review_line: Optional[str]
    visit_date: Optional[str]
    visit_count: Optional[str]
    receipt: Optional[str]

class ReviewDataDTO(BaseModel):
    reviews: List[ReviewDTO]

class BlogDataDTO(BaseModel):
    title: str
    author: str
    date: str
    content: str
    blog_url: str
    images: List[str]

class PhotoDataDTO(BaseModel):
    images: List[str]