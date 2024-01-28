from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.routes.cusine_crud import router as cuisine_crud_router
from app.routes.user_authentication import router as user_authentication_router

from app.utils.dependencies import validate_token

app = FastAPI(title="Cuisine API", description="API for cuisine details", version="1.0.0")

origins = [
        "http://localhost:3000",
]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)

app.include_router(user_authentication_router, tags=["User Authentication"], prefix="/user-authentication")
app.include_router(cuisine_crud_router, tags=["Cuisine CRUD"], prefix="/cuisine-crud", dependencies=[Depends(validate_token)])
