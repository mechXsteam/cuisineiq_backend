from typing import List

from fastapi import HTTPException, Depends, status, APIRouter, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.cuisine_details import CuisineDetails
from app.models.cuisine_images import CuisineImages
from app.schemas.cuisine_details import CuisineBase, CuisineUpdate
from app.schemas.users import User
from app.utils.dependencies import validate_token
from app.utils.helper_functions import validate_image_type, upload_file_to_s3, generate_tags, delete_file_from_s3

router = APIRouter()


@router.get("/my-cuisines", status_code=status.HTTP_200_OK)
async def get_my_cuisines(db: Session = Depends(get_db), current_user: User = Depends(validate_token)):
        """
        This route is used to get all the cuisines added by the user. It takes the user ID from the token and returns a list of all the cuisines added by the user.

        :param db:  Database session. \n
        :param current_user:  User details extracted from the token. \n

        :return:  List of all the cuisines added by the user. \n
        """
        try:
                # Step 1: Get the user ID from the token
                user_id = current_user.get('user_id')

                # Step 2: Get all the cuisines added by the user
                cuisines = CuisineDetails.get_cuisine_by_user_ID(db, user_id)
                cuisines_arr = [{**cuisine.__dict__, "images": [image.image_url for image in CuisineImages.get_cuisine_images(db, cuisine.id)]} for cuisine in cuisines]

                # Step 3: Return the response
                return {"message": "Cuisines fetched successfully", "cuisines": cuisines_arr}

        # Step 4: Handle exceptions
        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/", status_code=status.HTTP_200_OK)
async def get_cuisines(prompt: str = Query(None), db: Session = Depends(get_db)):
        """
        This route is used to get all the cuisines from the database. It returns a list of all the cuisines.

        :param prompt:  Prompt to search for a cuisine. \n
        :param db:  Database session. \n

        :return:  List of all the cuisines. \n
        """
        try:
                # Step 1: Get all the cuisines from the database
                cuisines = CuisineDetails.get_all_cuisines(db, prompt)

                # Step 2: Fetch all the images of the cuisines
                cuisines_arr = [{**cuisine.__dict__, "images": [image.image_url for image in CuisineImages.get_cuisine_images(db, cuisine.id)]} for cuisine in cuisines]

                # Step 3: Return the response
                return {"message": "Cuisines fetched successfully", "cuisines": cuisines_arr}

        # Step 4: Handle exceptions
        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/{cuisine_id}", status_code=status.HTTP_200_OK)
async def get_cuisine_by_ID(cuisine_id: str, db: Session = Depends(get_db)):
        """
        This route is used to get the details of a cuisine. It takes the cuisine ID as input and returns the details of the cuisine.

        :param cuisine_id:  ID of the cuisine meant to be fetched. \n
        :param db:  Database session. \n

        :return:  Details of the cuisine. \n

        :raises HTTPException 404:  Cuisine is not found. \n
        :raises HTTPException 500:  Internal Server Error. \n
        """
        try:
                # Step 1: Get the cuisine details from the database
                cuisine = CuisineDetails.get_cuisine_by_ID(db, cuisine_id)

                # Step 2: Check if the cuisine exists if no raises an HTTPException with status code 404 Not Found
                if cuisine is None:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuisine not found")

                # Step 3: Return the response
                return {"message": "Cuisine fetched successfully", "cuisine": {**cuisine.__dict__, "images": [image.image_url for image in CuisineImages.get_cuisine_images(db, cuisine.id)]}}

        # Step 4: Handle exceptions
        except HTTPException as error:
                raise error

        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.post("/add-cuisine", status_code=status.HTTP_201_CREATED)
async def add_cuisine(cuisine_details: CuisineBase, images: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(validate_token)):
        """
         This route is used to add a new cuisine to the database. It takes the cuisine details and images as input and returns a success message.

        :param cuisine_details: Cuisine details such as name, description, etc. \n
        :param images:  List of images of the cuisine. \n
        :param db:  Database session. \n
        :param current_user:  User details extracted from the token. \n

        :return:  Success message. \n

        :raises HTTPException 400:  Invalid image type. \n
        :raises HTTPException 500:  Internal Server Error. \n
        """
        try:
                # Step 1: Get the user ID from the token
                user_id = current_user.get('user_id')

                # Step 2: Generate tags from the description of the cuisine and create a new cuisine
                cuisine_tags = generate_tags(cuisine_details.description)
                cuisine = CuisineDetails.create_cuisine(db, user_id, **cuisine_details.model_dump(), **cuisine_tags)

                # Step 3: Upload the images to S3 and add the image URLs to the database
                for image in images:
                        if not validate_image_type(image.file):
                                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image type")
                        image_url = upload_file_to_s3(image, settings.S3_BUCKET)
                        CuisineImages.add_cuisine_images(db, cuisine.id, image_url)

                # Step 4: Return the response
                return {"message": "Cuisine added successfully"}

        # Step 5: Handle exceptions
        except HTTPException as error:
                raise error

        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.put("/update-cuisine/{cuisine_id}", status_code=status.HTTP_200_OK)
async def update_cuisine(cuisine_id: str, cuisine_details: CuisineUpdate, db: Session = Depends(get_db), current_user: User = Depends(validate_token)):
        """
        This route is used to update the details of a cuisine. It takes the cuisine ID and the updated cuisine details as input and returns a success message.
        The request body should not be passed as an empty JSON object. If you want to update only the description of the cuisine, pass the description in the request body.

        :param cuisine_id:  ID of the cuisine meant to be updated. \n
        :param cuisine_details:  Updated cuisine details. \n
        :param db:  Database session. \n
        :param current_user:  User details extracted from the token. \n

        :return:  Success message. \n

        :raises HTTPException 404:  Cuisine is not found. \n
        :raises HTTPException 403:  You are not the owner of this cuisine. \n
        :raises HTTPException 500:  Internal Server Error. \n
        """
        try:
                # Step 1: Get the user ID from the token
                user_id = current_user.get('user_id')

                # Step 2: Check if the cuisine exists if no raises an HTTPException with status code 404 Not Found
                cuisine = CuisineDetails.get_cuisine_by_ID(db, cuisine_id)
                if cuisine is None:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuisine not found")

                # Step 3: Check if the user is the owner of the cuisine if no raises an HTTPException with status code 403 Forbidden
                if cuisine.user_id != user_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of this cuisine")

                # Step 4: Update the cuisine details
                updated_description = cuisine_details.description
                if updated_description is not None:
                        # Step 4.1: Generate tags from the updated description
                        cuisine_tags = generate_tags(cuisine_details.description)
                        cuisine.update_cuisine(db, **cuisine_details.model_dump(), **cuisine_tags)
                else:
                        # Step 4.2: Update the cuisine details without generating tags
                        cuisine.update_cuisine(db, **cuisine_details.model_dump())

                # Step 5: Return the response
                return {"message": "Cuisine updated successfully", "updated_cuisine": cuisine}

        # Step 6: Handle exceptions
        except HTTPException as error:
                raise error

        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.delete("/delete_image/{image_id}", status_code=status.HTTP_200_OK)
async def delete_image(image_id: str, db: Session = Depends(get_db), current_user: User = Depends(validate_token)):
        """
        This route is used to delete an image of a cuisine. It takes the image ID as input and returns a success message.

        :param image_id:  ID of the image meant to be deleted. \n
        :param db:  Database session. \n
        :param current_user:  User details extracted from the token. \n

        :return:  Success message. \n

        :raises HTTPException 404:  The Image is not found. \n
        :raises HTTPException 403:  You are not the owner of this cuisine. \n
        :raises HTTPException 500:  Internal Server Error. \n
        """
        try:
                # Step 1: Get the user ID from the token
                user_id = current_user.get('user_id')

                # Step 2: Check if the image exists if no raises an HTTPException with status code 404 Not Found
                image = CuisineImages.get_cuisine_image_by_ID(db, image_id)
                if image is None:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

                # Step 3: Check if the user is the owner of the cuisine if no raises an HTTPException with status code 403 Forbidden
                cuisine = CuisineDetails.get_cuisine_by_ID(db, image.cuisine_id)
                if cuisine.user_id != user_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of this cuisine")

                # Step 4: Delete the image from S3 and the database
                image_url = image.image_url.split('/')[-1]
                delete_file_from_s3(image_url, settings.S3_BUCKET)
                CuisineImages.delete_image(db, image_id)

                # Step 5: Return the response
                return {"message": "Image deleted successfully"}

        # Step 6: Handle exceptions
        except HTTPException as error:
                raise error

        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.post("/add-images/{cuisine_id}", status_code=status.HTTP_201_CREATED)
async def add_images(cuisine_id: str, image: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(validate_token)):
        """
        This route is used to add images to a cuisine. It takes the cuisine ID and the image as input and returns a success message.

        :param cuisine_id:  ID of the cuisine to which images need to be added. \n
        :param image:  Image of the cuisine. \n
        :param db:  Database session. \n
        :param current_user:  User details extracted from the token. \n

        :return:  Success message. \n

        :raises HTTPException 404:  Cuisine is not found. \n
        :raises HTTPException 403:  You are not the owner of this cuisine. \n
        :raises HTTPException 400:  Invalid image type. \n
        """

        try:
                # Step 1: Get the user ID from the token
                user_id = current_user.get('user_id')

                # Step 2: Check if the cuisine exists if no raises an HTTPException with status code 404 Not Found
                cuisine = CuisineDetails.get_cuisine_by_ID(db, cuisine_id)
                if cuisine is None:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuisine not found")

                # Step 3: Check if the user is the owner of the cuisine if no raises an HTTPException with status code 403 Forbidden
                if cuisine.user_id != user_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of this cuisine")

                # Step 4: Upload the images to S3 and add the image URLs to the database
                if not validate_image_type(image.file):
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image type")
                image_url = upload_file_to_s3(image, settings.S3_BUCKET)
                CuisineImages.add_cuisine_images(db, cuisine_id, image_url)

                # Step 5: Return the response
                return {"message": "Images added successfully"}

        # Step 6: Handle exceptions
        except HTTPException as error:
                raise error

        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.delete("/delete-cuisine/{cuisine_id}", status_code=status.HTTP_200_OK)
async def delete_cuisine(cuisine_id: str, db: Session = Depends(get_db), current_user: User = Depends(validate_token)):
        """
        This route is used to delete a cuisine. It takes the cuisine ID as input and returns a success message.

        :param cuisine_id:  ID of the cuisine meant to be deleted. \n
        :param db:  Database session. \n
        :param current_user:  User details extracted from the token. \n
        :return:  Success message. \n
        """
        try:
                # Step 1: Get the user ID from the token
                user_id = current_user.get('user_id')

                # Step 2: Check if the cuisine exists if no raises an HTTPException with status code 404 Not Found
                cuisine = CuisineDetails.get_cuisine_by_ID(db, cuisine_id)
                if cuisine is None:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuisine not found")

                # Step 3: Check if the user is the owner of the cuisine if no raises an HTTPException with status code 403 Forbidden
                if cuisine.user_id != user_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of this cuisine")

                # Step 4: Delete the cuisine from the database
                CuisineDetails.delete_cuisine(db, cuisine_id)

                # Step 5: Return the response
                return {"message": "Cuisine deleted successfully"}

        # Step 6: Handle exceptions
        except HTTPException as error:
                raise error

        except Exception as error:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
