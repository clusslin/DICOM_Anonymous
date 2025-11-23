"""
Job management service for handling anonymization tasks
Manages the queue and execution of download/anonymization jobs
"""
import os
import shutil
import logging
import asyncio
import zipfile
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.anonymization_job import AnonymizationJob, JobStatus
from app.models.dicom_server import DicomServer
from app.services.dicom_service import DicomService
from app.services.anonymization_service import AnonymizationService
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing anonymization jobs"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._running_jobs: Dict[str, asyncio.Task] = {}

    async def create_job(
        self,
        server_id: int,
        study_instance_uid: str,
        series_instance_uid: str = None,
        patient_id: str = None,
        patient_name: str = None,
        study_date: str = None,
        study_description: str = None,
        modality: str = None,
        accession_number: str = None,
        anonymization_options: Dict = None,
        new_patient_id: str = None,
        new_patient_name: str = None,
        created_by: str = None
    ) -> AnonymizationJob:
        """Create a new anonymization job"""
        job = AnonymizationJob(
            job_uuid=str(uuid.uuid4()),
            server_id=server_id,
            patient_id=patient_id,
            patient_name=patient_name,
            study_instance_uid=study_instance_uid,
            series_instance_uid=series_instance_uid,
            study_date=study_date,
            study_description=study_description,
            modality=modality,
            accession_number=accession_number,
            anonymization_options=json.dumps(anonymization_options) if anonymization_options else None,
            new_patient_id=new_patient_id,
            new_patient_name=new_patient_name,
            status=JobStatus.PENDING,
            created_by=created_by
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def create_batch_jobs(
        self,
        server_id: int,
        items: List[Dict[str, Any]],
        anonymization_options: Dict = None,
        new_patient_id: str = None,
        new_patient_name: str = None,
        created_by: str = None
    ) -> List[AnonymizationJob]:
        """Create multiple jobs at once (batch)"""
        jobs = []

        for item in items:
            job = await self.create_job(
                server_id=server_id,
                study_instance_uid=item["study_instance_uid"],
                series_instance_uid=item.get("series_instance_uid"),
                patient_id=item.get("patient_id"),
                patient_name=item.get("patient_name"),
                study_date=item.get("study_date"),
                study_description=item.get("study_description"),
                modality=item.get("modality"),
                accession_number=item.get("accession_number"),
                anonymization_options=anonymization_options,
                new_patient_id=new_patient_id,
                new_patient_name=new_patient_name,
                created_by=created_by
            )
            jobs.append(job)

        return jobs

    async def get_job(self, job_uuid: str) -> Optional[AnonymizationJob]:
        """Get a job by UUID"""
        result = await self.db.execute(
            select(AnonymizationJob)
            .options(selectinload(AnonymizationJob.server))
            .where(AnonymizationJob.job_uuid == job_uuid)
        )
        return result.scalar_one_or_none()

    async def get_job_by_id(self, job_id: int) -> Optional[AnonymizationJob]:
        """Get a job by ID"""
        result = await self.db.execute(
            select(AnonymizationJob)
            .options(selectinload(AnonymizationJob.server))
            .where(AnonymizationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        status: JobStatus = None,
        created_by: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AnonymizationJob]:
        """List jobs with optional filtering"""
        query = select(AnonymizationJob).options(selectinload(AnonymizationJob.server))

        if status:
            query = query.where(AnonymizationJob.status == status)
        if created_by:
            query = query.where(AnonymizationJob.created_by == created_by)

        query = query.order_by(AnonymizationJob.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_job_status(
        self,
        job_uuid: str,
        status: JobStatus,
        progress: int = None,
        error_message: str = None,
        output_path: str = None,
        output_filename: str = None,
        total_instances: int = None,
        processed_instances: int = None
    ) -> Optional[AnonymizationJob]:
        """Update job status and progress"""
        job = await self.get_job(job_uuid)
        if not job:
            return None

        job.status = status

        if progress is not None:
            job.progress = progress
        if error_message:
            job.error_message = error_message
        if output_path:
            job.output_path = output_path
        if output_filename:
            job.output_filename = output_filename
        if total_instances is not None:
            job.total_instances = total_instances
        if processed_instances is not None:
            job.processed_instances = processed_instances

        if status == JobStatus.DOWNLOADING:
            job.started_at = datetime.utcnow()
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def cancel_job(self, job_uuid: str) -> bool:
        """Cancel a pending or running job"""
        job = await self.get_job(job_uuid)
        if not job:
            return False

        if job.status in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.DOWNLOADING, JobStatus.PROCESSING):
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            await self.db.commit()

            # Cancel running task if exists
            if job_uuid in self._running_jobs:
                self._running_jobs[job_uuid].cancel()
                del self._running_jobs[job_uuid]

            return True

        return False

    async def delete_job(self, job_uuid: str) -> bool:
        """Delete a job and its output files"""
        job = await self.get_job(job_uuid)
        if not job:
            return False

        # Cancel if running
        if job_uuid in self._running_jobs:
            self._running_jobs[job_uuid].cancel()
            del self._running_jobs[job_uuid]

        # Delete output files
        if job.output_path and os.path.exists(job.output_path):
            try:
                if os.path.isdir(job.output_path):
                    shutil.rmtree(job.output_path)
                else:
                    os.remove(job.output_path)
            except Exception as e:
                logger.warning(f"Failed to delete output files: {e}")

        await self.db.delete(job)
        await self.db.commit()

        return True

    async def process_job(self, job_uuid: str) -> Dict[str, Any]:
        """
        Process a single job: download, anonymize, and prepare for download
        """
        job = await self.get_job(job_uuid)
        if not job:
            return {"success": False, "error": "Job not found"}

        server = job.server
        if not server:
            await self.update_job_status(job_uuid, JobStatus.FAILED, error_message="Server not found")
            return {"success": False, "error": "Server not found"}

        try:
            # Update status to downloading
            await self.update_job_status(job_uuid, JobStatus.DOWNLOADING, progress=0)

            # Create DICOM service
            dicom_service = DicomService(
                ae_title=server.ae_title,
                host=server.host,
                port=server.port,
                local_ae_title=server.local_ae_title
            )

            # Create temp directory for download
            temp_dir = os.path.join(settings.DICOM_TEMP_DIR, job_uuid)
            os.makedirs(temp_dir, exist_ok=True)

            # Download images
            retrieve_result = dicom_service.retrieve_study(
                study_instance_uid=job.study_instance_uid,
                series_instance_uid=job.series_instance_uid,
                output_dir=temp_dir,
                use_get=server.supports_get,
                move_destination=server.move_destination_ae
            )

            if not retrieve_result["success"]:
                await self.update_job_status(
                    job_uuid,
                    JobStatus.FAILED,
                    error_message=f"Download failed: {retrieve_result.get('message', 'Unknown error')}"
                )
                return {"success": False, "error": "Download failed"}

            total_files = retrieve_result.get("received_count", 0)
            await self.update_job_status(
                job_uuid,
                JobStatus.PROCESSING,
                progress=30,
                total_instances=total_files
            )

            # Create output directory
            output_dir = os.path.join(settings.DICOM_OUTPUT_DIR, job_uuid)
            os.makedirs(output_dir, exist_ok=True)

            # Parse anonymization options
            anon_options = None
            if job.anonymization_options:
                anon_options = json.loads(job.anonymization_options)

            # Create anonymization service
            anon_service = AnonymizationService(
                new_patient_id=job.new_patient_id,
                new_patient_name=job.new_patient_name,
                anonymization_options=anon_options
            )

            # Anonymize files (preserve JPEG2000 transfer syntax)
            anon_result = anon_service.anonymize_directory(
                input_dir=temp_dir,
                output_dir=output_dir,
                preserve_transfer_syntax=True  # Critical: keep JPEG2000 format
            )

            if not anon_result["success"] and anon_result["processed_files"] == 0:
                await self.update_job_status(
                    job_uuid,
                    JobStatus.FAILED,
                    error_message="Anonymization failed for all files"
                )
                return {"success": False, "error": "Anonymization failed"}

            # Create ZIP file for download
            zip_filename = f"DICOM_ANON_{job.new_patient_id or job_uuid}_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
            zip_path = os.path.join(settings.DICOM_OUTPUT_DIR, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, output_dir)
                        zipf.write(file_path, arcname)

            # Update job with completion info
            await self.update_job_status(
                job_uuid,
                JobStatus.COMPLETED,
                progress=100,
                output_path=zip_path,
                output_filename=zip_filename,
                processed_instances=anon_result["processed_files"]
            )

            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            return {
                "success": True,
                "output_path": zip_path,
                "output_filename": zip_filename,
                "processed_files": anon_result["processed_files"]
            }

        except asyncio.CancelledError:
            await self.update_job_status(job_uuid, JobStatus.CANCELLED)
            raise
        except Exception as e:
            logger.error(f"Job processing failed: {e}")
            await self.update_job_status(
                job_uuid,
                JobStatus.FAILED,
                error_message=str(e)
            )
            return {"success": False, "error": str(e)}

    async def start_job_processing(self, job_uuid: str) -> None:
        """Start processing a job in the background"""
        task = asyncio.create_task(self.process_job(job_uuid))
        self._running_jobs[job_uuid] = task

    async def get_pending_jobs(self, limit: int = 10) -> List[AnonymizationJob]:
        """Get pending jobs for processing"""
        result = await self.db.execute(
            select(AnonymizationJob)
            .where(AnonymizationJob.status == JobStatus.PENDING)
            .order_by(AnonymizationJob.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def process_queue(self) -> None:
        """Process the job queue"""
        # Count currently running jobs
        running_count = len([t for t in self._running_jobs.values() if not t.done()])

        if running_count >= settings.MAX_CONCURRENT_DOWNLOADS:
            return

        # Get pending jobs
        available_slots = settings.MAX_CONCURRENT_DOWNLOADS - running_count
        pending_jobs = await self.get_pending_jobs(limit=available_slots)

        for job in pending_jobs:
            await self.start_job_processing(job.job_uuid)

    def cleanup_completed_tasks(self) -> None:
        """Clean up completed task references"""
        completed = [uuid for uuid, task in self._running_jobs.items() if task.done()]
        for uuid in completed:
            del self._running_jobs[uuid]
