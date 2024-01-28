import uuid

from sqlalchemy import Column, String, DateTime

from app.database import Base
from app.utils.helper_functions import get_current_time, generate_tags


class CuisineDetails(Base):
        __tablename__ = "cuisine_details"

        id = Column(String(36), primary_key=True, default=str(uuid.uuid4()), unique=True, nullable=False)
        user_id = Column(String(36), nullable=False)
        name = Column(String(255), nullable=False)
        description = Column(String(255), nullable=False)
        latitude = Column(String(255), nullable=False)
        longitude = Column(String(255), nullable=False)
        cuisine = Column(String(255), nullable=False)
        budget = Column(String(255), nullable=False)
        ambience = Column(String(255), nullable=False)
        dietary_options = Column(String(255), nullable=False)
        created_at = Column(DateTime, default=get_current_time())
        updated_at = Column(DateTime, default=get_current_time(), onupdate=get_current_time())

        def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.id = self.id or str(uuid.uuid4())

        @classmethod
        def get_all_cuisines(cls, db, prompt=None):
                tags = generate_tags(prompt) if prompt else None
                query = db.query(cls)
                if tags:
                        if 'cuisine' in tags:
                                query = query.filter(cls.cuisine == tags['cuisine'])
                        if 'budget' in tags:
                                query = query.filter(cls.budget == tags['budget'])
                        if 'ambience' in tags:
                                query = query.filter(cls.ambience == tags['ambience'])
                        if 'dietary_options' in tags:
                                query = query.filter(cls.dietary_options == tags['dietary_options'])
                return query.all()

        @classmethod
        def get_cuisine_by_ID(cls, db, cuisine_id):
                return db.query(cls).filter(cls.id == cuisine_id).first()

        @classmethod
        def get_cuisine_by_user_ID(cls, db, user_id):
                return db.query(cls).filter(cls.user_id == user_id).all()

        @classmethod
        def create_cuisine(cls, db, user_id, **kwargs):
                cuisine = cls(user_id=user_id, **kwargs)
                db.add(cuisine)
                db.commit()
                db.refresh(cuisine)
                return cuisine

        @classmethod
        def update_cuisine(cls, db, **kwargs):
                cuisine_to_update = db.query(cls).filter(cls.id == kwargs['id']).first()
                for key, value in kwargs.items():
                        if value is not None:
                                setattr(cuisine_to_update, key, value)
                db.commit()
                db.refresh(cuisine_to_update)
                return cuisine_to_update

        @classmethod
        def delete_cuisine(cls, db, cuisine_id):
                cuisine_to_delete = db.query(cls).filter(cls.id == cuisine_id).first()
                db.delete(cuisine_to_delete)
                db.commit()
                return True
