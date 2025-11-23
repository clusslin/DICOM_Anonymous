"""
DICOM Query API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.dicom_server import DicomServer
from app.schemas.dicom_query import (
    PatientQuery,
    StudyQuery,
    PatientResult,
    StudyResult,
    SeriesResult,
    StudyWithSeriesResult,
    QueryResponse
)
from app.services.dicom_service import DicomService

router = APIRouter(prefix="/query", tags=["DICOM Query"])


async def get_server(server_id: int, db: AsyncSession) -> DicomServer:
    """Helper to get server or raise 404"""
    result = await db.execute(
        select(DicomServer).where(DicomServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    if not server.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server is not active"
        )

    return server


@router.get("/patients", response_model=QueryResponse)
async def query_patients(
    server_id: int,
    patient_name: Optional[str] = Query(None, description="Patient name (use * for wildcard)"),
    patient_id: Optional[str] = Query(None, description="Patient ID"),
    birth_date: Optional[str] = Query(None, description="Birth date (YYYYMMDD)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Query for patients on a DICOM server
    """
    server = await get_server(server_id, db)

    dicom_service = DicomService(
        ae_title=server.ae_title,
        host=server.host,
        port=server.port,
        local_ae_title=server.local_ae_title
    )

    try:
        results = dicom_service.find_patients(
            patient_name=patient_name or "",
            patient_id=patient_id or "",
            birth_date=birth_date or ""
        )

        return QueryResponse(
            success=True,
            count=len(results),
            results=results
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            count=0,
            results=[],
            message=str(e)
        )


@router.get("/studies", response_model=QueryResponse)
async def query_studies(
    server_id: int,
    patient_name: Optional[str] = Query(None, description="Patient name (use * for wildcard)"),
    patient_id: Optional[str] = Query(None, description="Patient ID"),
    study_date: Optional[str] = Query(None, description="Study date (YYYYMMDD)"),
    study_date_from: Optional[str] = Query(None, description="Study date range start"),
    study_date_to: Optional[str] = Query(None, description="Study date range end"),
    modality: Optional[str] = Query(None, description="Modality (CT, MR, CR, etc.)"),
    accession_number: Optional[str] = Query(None, description="Accession number"),
    study_description: Optional[str] = Query(None, description="Study description"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Query for studies on a DICOM server with multiple filter options
    """
    server = await get_server(server_id, db)

    dicom_service = DicomService(
        ae_title=server.ae_title,
        host=server.host,
        port=server.port,
        local_ae_title=server.local_ae_title
    )

    # Build date range if specified
    study_date_range = ""
    if study_date_from and study_date_to:
        study_date_range = f"{study_date_from}-{study_date_to}"
    elif study_date_from:
        study_date_range = f"{study_date_from}-"
    elif study_date_to:
        study_date_range = f"-{study_date_to}"

    try:
        results = dicom_service.find_studies(
            patient_name=patient_name or "",
            patient_id=patient_id or "",
            study_date=study_date or "",
            study_date_range=study_date_range,
            modality=modality or "",
            accession_number=accession_number or "",
            study_description=study_description or ""
        )

        return QueryResponse(
            success=True,
            count=len(results),
            results=results
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            count=0,
            results=[],
            message=str(e)
        )


@router.get("/series/{study_instance_uid}", response_model=QueryResponse)
async def query_series(
    study_instance_uid: str,
    server_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Query for series within a specific study
    """
    server = await get_server(server_id, db)

    dicom_service = DicomService(
        ae_title=server.ae_title,
        host=server.host,
        port=server.port,
        local_ae_title=server.local_ae_title
    )

    try:
        results = dicom_service.find_series(study_instance_uid)

        return QueryResponse(
            success=True,
            count=len(results),
            results=results
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            count=0,
            results=[],
            message=str(e)
        )


@router.get("/study-with-series", response_model=QueryResponse)
async def query_studies_with_series(
    server_id: int,
    patient_name: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    study_date: Optional[str] = Query(None),
    study_date_from: Optional[str] = Query(None),
    study_date_to: Optional[str] = Query(None),
    modality: Optional[str] = Query(None),
    accession_number: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Query for studies and automatically fetch their series information
    """
    server = await get_server(server_id, db)

    dicom_service = DicomService(
        ae_title=server.ae_title,
        host=server.host,
        port=server.port,
        local_ae_title=server.local_ae_title
    )

    # Build date range
    study_date_range = ""
    if study_date_from and study_date_to:
        study_date_range = f"{study_date_from}-{study_date_to}"
    elif study_date_from:
        study_date_range = f"{study_date_from}-"
    elif study_date_to:
        study_date_range = f"-{study_date_to}"

    try:
        # First get studies
        studies = dicom_service.find_studies(
            patient_name=patient_name or "",
            patient_id=patient_id or "",
            study_date=study_date or "",
            study_date_range=study_date_range,
            modality=modality or "",
            accession_number=accession_number or ""
        )

        # Then fetch series for each study
        results = []
        for study in studies:
            study_uid = study.get("StudyInstanceUID")
            if study_uid:
                series = dicom_service.find_series(study_uid)
                study["series"] = series
            else:
                study["series"] = []
            results.append(study)

        return QueryResponse(
            success=True,
            count=len(results),
            results=results
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            count=0,
            results=[],
            message=str(e)
        )
