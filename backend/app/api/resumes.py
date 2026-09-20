from fastapi import APIRouter, Depends, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.models.orm import Resume, User
from app.pipelines.document_extractor import DocumentParseError, UnsupportedFileTypeError
from app.pipelines.resume_parser import parse_resume

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


class ResumeSummary(BaseModel):
    id: str
    filename: str
    used_ocr: bool

    class Config:
        from_attributes = True


class ResumeDetail(ResumeSummary):
    parsed: dict


@router.post("/upload", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    settings = get_settings()
    file_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise AppError(413, "FILE_TOO_LARGE", f"File exceeds {settings.max_file_size_mb}MB limit.")
    if not file.filename:
        raise AppError(400, "MISSING_FILENAME", "Uploaded file has no filename.")

    try:
        parsed = parse_resume(file_bytes, file.filename)
    except UnsupportedFileTypeError as exc:
        raise AppError(400, "UNSUPPORTED_FILE_TYPE", str(exc)) from exc
    except DocumentParseError as exc:
        raise AppError(422, "RESUME_PARSE_FAILED", str(exc)) from exc

    resume = Resume(
        owner_id=user.id if user else None,
        filename=file.filename,
        raw_text=parsed.raw_text,
        parsed_json=parsed.to_dict(),
        used_ocr=parsed.used_ocr,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return ResumeDetail(id=resume.id, filename=resume.filename, used_ocr=resume.used_ocr, parsed=resume.parsed_json)


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(resume_id: str, db: Session = Depends(get_db)):
    resume = db.get(Resume, resume_id)
    if not resume:
        raise AppError(404, "RESUME_NOT_FOUND", "Resume not found.")
    return ResumeDetail(id=resume.id, filename=resume.filename, used_ocr=resume.used_ocr, parsed=resume.parsed_json)
