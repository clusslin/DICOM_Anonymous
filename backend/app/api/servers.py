"""
DICOM Server management API endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user, get_admin_user
from app.models.dicom_server import DicomServer
from app.schemas.dicom_server import (
    DicomServerCreate,
    DicomServerUpdate,
    DicomServerResponse,
    ConnectionTestResult
)
from app.services.dicom_service import DicomService

router = APIRouter(prefix="/servers", tags=["DICOM Servers"])


@router.get("", response_model=list[DicomServerResponse])
async def list_servers(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all DICOM servers
    """
    result = await db.execute(
        select(DicomServer).order_by(DicomServer.name)
    )
    return list(result.scalars().all())


@router.get("/active", response_model=list[DicomServerResponse])
async def list_active_servers(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List active DICOM servers only
    """
    result = await db.execute(
        select(DicomServer)
        .where(DicomServer.is_active == True)
        .order_by(DicomServer.name)
    )
    return list(result.scalars().all())


@router.get("/{server_id}", response_model=DicomServerResponse)
async def get_server(
    server_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific DICOM server
    """
    result = await db.execute(
        select(DicomServer).where(DicomServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    return server


@router.post("", response_model=DicomServerResponse)
async def create_server(
    server_data: DicomServerCreate,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new DICOM server configuration (admin only)
    """
    # If this is set as default, unset other defaults
    if server_data.is_default:
        result = await db.execute(
            select(DicomServer).where(DicomServer.is_default == True)
        )
        for existing in result.scalars().all():
            existing.is_default = False

    server = DicomServer(**server_data.model_dump())
    db.add(server)
    await db.commit()
    await db.refresh(server)

    return server


@router.put("/{server_id}", response_model=DicomServerResponse)
async def update_server(
    server_id: int,
    server_data: DicomServerUpdate,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a DICOM server configuration (admin only)
    """
    result = await db.execute(
        select(DicomServer).where(DicomServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    # If setting as default, unset other defaults
    if server_data.is_default:
        result = await db.execute(
            select(DicomServer).where(
                DicomServer.is_default == True,
                DicomServer.id != server_id
            )
        )
        for existing in result.scalars().all():
            existing.is_default = False

    # Update fields
    update_data = server_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)

    await db.commit()
    await db.refresh(server)

    return server


@router.delete("/{server_id}")
async def delete_server(
    server_id: int,
    current_user: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a DICOM server configuration (admin only)
    """
    result = await db.execute(
        select(DicomServer).where(DicomServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    await db.delete(server)
    await db.commit()

    return {"message": "Server deleted successfully"}


@router.post("/{server_id}/test", response_model=ConnectionTestResult)
async def test_connection(
    server_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test connection to a DICOM server using C-ECHO
    """
    result = await db.execute(
        select(DicomServer).where(DicomServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    # Create DICOM service and test connection
    dicom_service = DicomService(
        ae_title=server.ae_title,
        host=server.host,
        port=server.port,
        local_ae_title=server.local_ae_title
    )

    test_result = dicom_service.verify_connection()

    # Update last verified timestamp if successful
    if test_result["success"]:
        server.last_verified_at = datetime.utcnow()
        await db.commit()

    return ConnectionTestResult(**test_result)


@router.get("/default", response_model=DicomServerResponse)
async def get_default_server(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the default DICOM server
    """
    result = await db.execute(
        select(DicomServer).where(DicomServer.is_default == True)
    )
    server = result.scalar_one_or_none()

    if not server:
        # Return first active server if no default is set
        result = await db.execute(
            select(DicomServer)
            .where(DicomServer.is_active == True)
            .limit(1)
        )
        server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No DICOM server configured"
        )

    return server
