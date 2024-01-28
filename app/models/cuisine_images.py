import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime

from app.database import Base
from app.utils.helper_functions import get_current_time


class CuisineImages(Base):
        __tablename__ = "cuisine_images"

        id = Column(String(36), primary_key=True, default=str(uuid.uuid4()), unique=True, nullable=False)
        cuisine_id = Column(String(36), ForeignKey('cuisine_details.id', onupdate='CASCADE'), nullable=False)
        image_url = Column(String(255), nullable=False)
        created_at = Column(DateTime, default=get_current_time())
        updated_at = Column(DateTime, default=get_current_time(), onupdate=get_current_time())

        def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.id = self.id or str(uuid.uuid4())

        @classmethod
        def get_cuisine_images(cls, db, cuisine_id):
                return db.query(cls).filter(cls.cuisine_id == cuisine_id).all()

        @classmethod
        def get_cuisine_image_by_ID(cls, db, image_id):
                return db.query(cls).filter(cls.id == image_id).first()

        @classmethod
        def add_cuisine_images(cls, db, cuisine_id, image_url):
                cuisine_image = cls(cuisine_id=cuisine_id, image_url=image_url)
                db.add(cuisine_image)
                db.commit()
                db.refresh(cuisine_image)
                return cuisine_image

        @classmethod
        def delete_image(cls, db, image_id):
                cuisine_image = cls.get_cuisine_image_by_ID(db, image_id)
                db.delete(cuisine_image)
                db.commit()
                return True
