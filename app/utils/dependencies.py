import jwt
from fastapi import HTTPException, status, Depends, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.users import Users


def validate_token(token: str = Header(...), db: Session = Depends(get_db)):
        try:
                # Step 1: Decode the token
                user_details = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

                # Step 2: Extract user ID and email from the decoded token
                user_id = user_details.get('user_id')
                user = Users.get_user_by_ID(db, user_id)

                # Step 3: Check if the user exists, if no raises an HTTPException with status code 401 Unauthorized else return the token for further processing
                if user is None:
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

                return user_details

        # Step 4: Handle exceptions
        except HTTPException as error:
                raise error

        except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

        except jwt.InvalidTokenError:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

        except Exception as e:
                raise e
