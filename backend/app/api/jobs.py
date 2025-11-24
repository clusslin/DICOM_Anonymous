"""
Anonymization Jobs API endpoints
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.anonymization_job import AnonymizationJob, JobStatus as ModelJobStatus
from app.models.dicom_server import DicomServer
from app.models.anonymization_config import DEFAULT_ANONYMIZATION_TAGS
from app.schemas.anonymization import (
    JobCreate,
    BatchJobCreate,
    JobResponse,
    JobStatusUpdate,
    JobListResponse,
    JobStatus,
    DefaultAnonymizationTagsResponse
)
from app.services.job_service import JobService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/jobs", tags=["Anonymization Jobs"])


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for X-Forwarded-For header (if behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


@router.post("", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new anonymization job
    """
    # Verify server exists
    result = await db.execute(
        select(DicomServer).where(DicomServer.id == job_data.server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    # Get client IP
    client_ip = get_client_ip(request)

    job_service = JobService(db)

    # Convert anonymization options to dict
    anon_options = None
    if job_data.anonymization_options:
        anon_options = job_data.anonymization_options.to_tag_config()

    job = await job_service.create_job(
        server_id=job_data.server_id,
        study_instance_uid=job_data.study_instance_uid,
        series_instance_uid=job_data.series_instance_uid,
        patient_id=job_data.patient_id,
        patient_name=job_data.patient_name,
        study_date=job_data.study_date,
        study_description=job_data.study_description,
        modality=job_data.modality,
        accession_number=job_data.accession_number,
        anonymization_options=anon_options,
        new_patient_id=job_data.new_patient_id,
        new_patient_name=job_data.new_patient_name,
        created_by=current_user["username"],
        request_reason=job_data.request_reason,
        client_ip=client_ip
    )

    # Log audit
    audit_service = AuditService(db)
    await audit_service.log_job_created(
        job_uuid=job.job_uuid,
        username=current_user["username"],
        client_ip=client_ip,
        request_reason=job_data.request_reason,
        study_info={
            "patient_id": job_data.patient_id,
            "patient_name": job_data.patient_name,
            "study_date": job_data.study_date,
            "study_instance_uid": job_data.study_instance_uid
        },
        user_agent=request.headers.get("User-Agent")
    )

    # Start processing in background
    background_tasks.add_task(job_service.process_job, job.job_uuid)

    return job


@router.post("/batch", response_model=list[JobResponse])
async def create_batch_jobs(
    batch_data: BatchJobCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create multiple anonymization jobs at once
    """
    # Verify server exists
    result = await db.execute(
        select(DicomServer).where(DicomServer.id == batch_data.server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    # Get client IP
    client_ip = get_client_ip(request)

    job_service = JobService(db)
    audit_service = AuditService(db)

    # Convert anonymization options
    anon_options = None
    if batch_data.anonymization_options:
        anon_options = batch_data.anonymization_options.to_tag_config()

    # Convert items to dict format
    items = [item.model_dump() for item in batch_data.items]

    jobs = await job_service.create_batch_jobs(
        server_id=batch_data.server_id,
        items=items,
        anonymization_options=anon_options,
        new_patient_id=batch_data.new_patient_id,
        new_patient_name=batch_data.new_patient_name,
        created_by=current_user["username"],
        request_reason=batch_data.request_reason,
        client_ip=client_ip
    )

    # Log audit for each job
    for job in jobs:
        await audit_service.log_job_created(
            job_uuid=job.job_uuid,
            username=current_user["username"],
            client_ip=client_ip,
            request_reason=batch_data.request_reason,
            study_info={
                "study_instance_uid": job.study_instance_uid,
                "patient_id": job.patient_id,
                "patient_name": job.patient_name
            },
            user_agent=request.headers.get("User-Agent")
        )

    # Start processing jobs sequentially in background
    for job in jobs:
        background_tasks.add_task(job_service.process_job, job.job_uuid)

    return jobs


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status_filter: Optional[JobStatus] = None,
    my_jobs_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List anonymization jobs
    """
    job_service = JobService(db)

    # Convert API status to model status
    model_status = None
    if status_filter:
        model_status = ModelJobStatus(status_filter.value)

    created_by = current_user["username"] if my_jobs_only else None

    jobs = await job_service.list_jobs(
        status=model_status,
        created_by=created_by,
        limit=limit,
        offset=offset
    )

    # Get total count
    query = select(func.count(AnonymizationJob.id))
    if model_status:
        query = query.where(AnonymizationJob.status == model_status)
    if created_by:
        query = query.where(AnonymizationJob.created_by == created_by)
    result = await db.execute(query)
    total = result.scalar()

    return JobListResponse(
        total=total,
        jobs=jobs
    )


@router.get("/{job_uuid}", response_model=JobResponse)
async def get_job(
    job_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific job by UUID
    """
    job_service = JobService(db)
    job = await job_service.get_job(job_uuid)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.post("/{job_uuid}/cancel")
async def cancel_job(
    job_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a pending or running job
    """
    job_service = JobService(db)

    success = await job_service.cancel_job(job_uuid)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled (not found or already completed)"
        )

    return {"message": "Job cancelled successfully"}


@router.delete("/{job_uuid}")
async def delete_job(
    job_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a job and its output files
    """
    job_service = JobService(db)

    success = await job_service.delete_job(job_uuid)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return {"message": "Job deleted successfully"}


@router.get("/{job_uuid}/download")
async def download_job_result(
    job_uuid: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download the anonymized DICOM files for a completed job
    """
    job_service = JobService(db)
    job = await job_service.get_job(job_uuid)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status != ModelJobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {job.status.value})"
        )

    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found"
        )

    # Log audit for download
    client_ip = get_client_ip(request)
    audit_service = AuditService(db)
    await audit_service.log_job_downloaded(
        job_uuid=job_uuid,
        username=current_user["username"],
        client_ip=client_ip,
        filename=job.output_filename,
        user_agent=request.headers.get("User-Agent")
    )

    return FileResponse(
        path=job.output_path,
        filename=job.output_filename or "dicom_anonymized.zip",
        media_type="application/zip"
    )


@router.get("/config/default-tags", response_model=DefaultAnonymizationTagsResponse)
async def get_default_anonymization_tags(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the default anonymization tag configuration
    """
    return DefaultAnonymizationTagsResponse(tags=DEFAULT_ANONYMIZATION_TAGS)
