from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_colorize_service
from app.application.services.colorize_service import ColorizeImageService

router = APIRouter(prefix="/images", tags=["images"])

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


@router.post("/colorize")
async def colorize_image(
    file: UploadFile = File(...),
    service: ColorizeImageService = Depends(get_colorize_service),
) -> Response:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Use png/jpg/jpeg/webp.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    result = service.execute(image_bytes=image_bytes)
    return Response(content=result.image_bytes, media_type=result.content_type)
