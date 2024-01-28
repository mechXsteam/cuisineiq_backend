import uuid
from datetime import datetime, timedelta

import jwt
from sqlalchemy import Column, String, DateTime

from app.config import settings
from app.database import Base
from app.utils.helper_functions import get_current_time


class Users(Base):
        __tablename__ = "users"

        id = Column(String(36), primary_key=True, default=str(uuid.uuid4()), unique=True, nullable=False)
        name = Column(String(255), nullable=False)
        phone_number = Column(String(15), nullable=False)
        email = Column(String(255), nullable=True)
        otp_secret = Column(String(255), nullable=False)
        created_at = Column(DateTime, nullable=False, default=get_current_time)
        updated_at = Column(DateTime, default=get_current_time, onupdate=get_current_time)

        def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.id = self.id or str(uuid.uuid4())

        @classmethod
        def get_user_by_phone_number(cls, db, phone_number):
                return db.query(cls).filter(cls.phone_number == phone_number).first()

        @classmethod
        def get_user_by_ID(cls, db, user_id):
                return db.query(cls).filter(cls.id == user_id).first()

        @classmethod
        def create_user(cls, db, **kwargs):
                user = cls(**kwargs)
                db.add(user)
                db.commit()
                db.refresh(user)
                return user

        @classmethod
        def generate_access_token(cls, db, phone_number):
                user = cls.get_user_by_phone_number(db, phone_number)
                access_token_expires = datetime.utcnow() + timedelta(minutes=60)
                access_token_payload = {"user_id": user.id, "name": user.name, "email": user.email, "exp": access_token_expires}
                access_token = jwt.encode(access_token_payload, settings.SECRET_KEY, algorithm="HS256")
                return access_token
