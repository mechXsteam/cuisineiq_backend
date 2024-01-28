from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# create sqlalchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# creating session local class, each instance of this session local class will be a database session in itself
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create a base class
Base = declarative_base()


def get_db():
        db = SessionLocal()
        try:
                yield db
        finally:
                db.close()
