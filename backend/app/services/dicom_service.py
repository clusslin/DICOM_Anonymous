"""
DICOM communication service using pynetdicom
Handles C-ECHO, C-FIND, C-GET/C-MOVE operations
"""
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from pynetdicom import AE, evt, StoragePresentationContexts
from pynetdicom.sop_class import (
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelGet,
    PatientRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelMove,
    Verification,
)
from pydicom.dataset import Dataset
from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian

from app.core.config import settings
from app.services.settings_service import get_cached_setting

logger = logging.getLogger(__name__)


class DicomService:
    """DICOM communication service"""

    def __init__(
        self,
        ae_title: str,
        host: str,
        port: int,
        local_ae_title: str = None
    ):
        self.ae_title = ae_title
        self.host = host
        self.port = port
        self.local_ae_title = local_ae_title or get_cached_setting(
            "dicom.local_ae_title",
            settings.DICOM_AE_TITLE
        )

    def verify_connection(self) -> Dict[str, Any]:
        """
        Test connection to DICOM server using C-ECHO
        """
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(Verification)

        try:
            assoc = ae.associate(self.host, self.port, ae_title=self.ae_title)
            if assoc.is_established:
                status = assoc.send_c_echo()
                assoc.release()
                if status:
                    return {
                        "success": True,
                        "message": "Connection successful",
                        "status_code": status.Status
                    }
                return {
                    "success": False,
                    "message": "C-ECHO failed - no status returned"
                }
            return {
                "success": False,
                "message": f"Association rejected: {assoc.acceptor.primitive}"
            }
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return {
                "success": False,
                "message": str(e)
            }

    def find_patients(
        self,
        patient_name: str = "",
        patient_id: str = "",
        birth_date: str = "",
        accession_number: str = "",
        study_date: str = "",
        modality: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Query for patients using C-FIND at PATIENT level
        """
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

        # Build query dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = "PATIENT"
        ds.PatientName = patient_name if patient_name else "*"
        ds.PatientID = patient_id if patient_id else "*"
        ds.PatientBirthDate = birth_date if birth_date else ""
        ds.PatientSex = ""
        ds.NumberOfPatientRelatedStudies = ""

        results = []

        try:
            assoc = ae.associate(self.host, self.port, ae_title=self.ae_title)
            if assoc.is_established:
                responses = assoc.send_c_find(
                    ds,
                    PatientRootQueryRetrieveInformationModelFind
                )

                for status, identifier in responses:
                    if status and status.Status in (0xFF00, 0xFF01) and identifier:
                        results.append({
                            "PatientName": str(identifier.PatientName) if "PatientName" in identifier else "",
                            "PatientID": str(identifier.PatientID) if "PatientID" in identifier else "",
                            "PatientBirthDate": str(identifier.PatientBirthDate) if "PatientBirthDate" in identifier else "",
                            "PatientSex": str(identifier.PatientSex) if "PatientSex" in identifier else "",
                            "NumberOfPatientRelatedStudies": str(identifier.NumberOfPatientRelatedStudies) if "NumberOfPatientRelatedStudies" in identifier else ""
                        })

                assoc.release()
        except Exception as e:
            logger.error(f"Patient query failed: {e}")

        return results

    def find_studies(
        self,
        patient_id: str = "",
        patient_name: str = "",
        study_date: str = "",
        study_date_range: str = "",
        modality: str = "",
        accession_number: str = "",
        study_description: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Query for studies using C-FIND at STUDY level
        """
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

        # Build query dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = "STUDY"

        # Patient info
        ds.PatientName = patient_name if patient_name else ""
        ds.PatientID = patient_id if patient_id else ""
        ds.PatientBirthDate = ""
        ds.PatientSex = ""

        # Study info
        if study_date_range:
            ds.StudyDate = study_date_range
        elif study_date:
            ds.StudyDate = study_date
        else:
            ds.StudyDate = ""

        ds.StudyTime = ""
        ds.AccessionNumber = accession_number if accession_number else ""
        ds.StudyID = ""
        ds.StudyInstanceUID = ""
        ds.StudyDescription = study_description if study_description else ""
        ds.ModalitiesInStudy = modality if modality else ""
        ds.NumberOfStudyRelatedSeries = ""
        ds.NumberOfStudyRelatedInstances = ""

        results = []

        try:
            assoc = ae.associate(self.host, self.port, ae_title=self.ae_title)
            if assoc.is_established:
                responses = assoc.send_c_find(
                    ds,
                    StudyRootQueryRetrieveInformationModelFind
                )

                for status, identifier in responses:
                    if status and status.Status in (0xFF00, 0xFF01) and identifier:
                        results.append({
                            "PatientName": str(identifier.PatientName) if "PatientName" in identifier else "",
                            "PatientID": str(identifier.PatientID) if "PatientID" in identifier else "",
                            "PatientBirthDate": str(identifier.PatientBirthDate) if "PatientBirthDate" in identifier else "",
                            "PatientSex": str(identifier.PatientSex) if "PatientSex" in identifier else "",
                            "StudyInstanceUID": str(identifier.StudyInstanceUID) if "StudyInstanceUID" in identifier else "",
                            "StudyDate": str(identifier.StudyDate) if "StudyDate" in identifier else "",
                            "StudyTime": str(identifier.StudyTime) if "StudyTime" in identifier else "",
                            "StudyDescription": str(identifier.StudyDescription) if "StudyDescription" in identifier else "",
                            "AccessionNumber": str(identifier.AccessionNumber) if "AccessionNumber" in identifier else "",
                            "StudyID": str(identifier.StudyID) if "StudyID" in identifier else "",
                            "ModalitiesInStudy": str(identifier.ModalitiesInStudy) if "ModalitiesInStudy" in identifier else "",
                            "NumberOfStudyRelatedSeries": str(identifier.NumberOfStudyRelatedSeries) if "NumberOfStudyRelatedSeries" in identifier else "",
                            "NumberOfStudyRelatedInstances": str(identifier.NumberOfStudyRelatedInstances) if "NumberOfStudyRelatedInstances" in identifier else ""
                        })

                assoc.release()
        except Exception as e:
            logger.error(f"Study query failed: {e}")

        return results

    def find_series(self, study_instance_uid: str) -> List[Dict[str, Any]]:
        """
        Query for series within a study using C-FIND at SERIES level
        """
        ae = AE(ae_title=self.local_ae_title)
        ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

        # Build query dataset
        ds = Dataset()
        ds.QueryRetrieveLevel = "SERIES"
        ds.StudyInstanceUID = study_instance_uid

        # Series info to retrieve
        ds.SeriesInstanceUID = ""
        ds.SeriesNumber = ""
        ds.SeriesDescription = ""
        ds.SeriesDate = ""
        ds.SeriesTime = ""
        ds.Modality = ""
        ds.BodyPartExamined = ""
        ds.NumberOfSeriesRelatedInstances = ""
        ds.ProtocolName = ""

        results = []

        try:
            assoc = ae.associate(self.host, self.port, ae_title=self.ae_title)
            if assoc.is_established:
                responses = assoc.send_c_find(
                    ds,
                    StudyRootQueryRetrieveInformationModelFind
                )

                for status, identifier in responses:
                    if status and status.Status in (0xFF00, 0xFF01) and identifier:
                        results.append({
                            "SeriesInstanceUID": str(identifier.SeriesInstanceUID) if "SeriesInstanceUID" in identifier else "",
                            "SeriesNumber": str(identifier.SeriesNumber) if "SeriesNumber" in identifier else "",
                            "SeriesDescription": str(identifier.SeriesDescription) if "SeriesDescription" in identifier else "",
                            "SeriesDate": str(identifier.SeriesDate) if "SeriesDate" in identifier else "",
                            "SeriesTime": str(identifier.SeriesTime) if "SeriesTime" in identifier else "",
                            "Modality": str(identifier.Modality) if "Modality" in identifier else "",
                            "BodyPartExamined": str(identifier.BodyPartExamined) if "BodyPartExamined" in identifier else "",
                            "NumberOfSeriesRelatedInstances": str(identifier.NumberOfSeriesRelatedInstances) if "NumberOfSeriesRelatedInstances" in identifier else "",
                            "ProtocolName": str(identifier.ProtocolName) if "ProtocolName" in identifier else ""
                        })

                assoc.release()

        except Exception as e:
            logger.error(f"Series query failed: {e}")

        # Sort by series number
        results.sort(key=lambda x: int(x["SeriesNumber"]) if x["SeriesNumber"].isdigit() else 0)
        return results

    def retrieve_study(
        self,
        study_instance_uid: str,
        output_dir: str,
        series_instance_uid: str = None,
        use_get: bool = True,
        move_destination: str = None
    ) -> Dict[str, Any]:
        """
        Retrieve images from DICOM server using C-GET or C-MOVE
        """
        received_files = []
        errors = []

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        def handle_store(event):
            """Handle incoming C-STORE requests"""
            ds = event.dataset
            ds.file_meta = event.file_meta

            # Generate filename
            sop_instance_uid = ds.SOPInstanceUID
            filename = os.path.join(output_dir, f"{sop_instance_uid}.dcm")

            # Save the dataset - preserve original transfer syntax (JPEG2000)
            ds.save_as(filename, write_like_original=True)
            received_files.append(filename)
            return 0x0000  # Success

        ae = AE(ae_title=self.local_ae_title)

        # Add storage presentation contexts for receiving images
        # Include JPEG2000 transfer syntaxes
        storage_contexts = StoragePresentationContexts
        for context in storage_contexts:
            ae.add_requested_context(context.abstract_syntax)

        if use_get:
            ae.add_requested_context(StudyRootQueryRetrieveInformationModelGet)
            ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
        else:
            ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)
            ae.add_requested_context(PatientRootQueryRetrieveInformationModelMove)

        # Add supported transfer syntaxes including JPEG2000
        transfer_syntaxes = [
            "1.2.840.10008.1.2",       # Implicit VR Little Endian
            "1.2.840.10008.1.2.1",     # Explicit VR Little Endian
            "1.2.840.10008.1.2.2",     # Explicit VR Big Endian
            "1.2.840.10008.1.2.4.90",  # JPEG 2000 Lossless
            "1.2.840.10008.1.2.4.91",  # JPEG 2000 Lossy
            "1.2.840.10008.1.2.4.70",  # JPEG Lossless
            "1.2.840.10008.1.2.4.50",  # JPEG Baseline
            "1.2.840.10008.1.2.4.51",  # JPEG Extended
            "1.2.840.10008.1.2.5",     # RLE Lossless
        ]

        # Build query dataset
        ds = Dataset()
        if series_instance_uid:
            ds.QueryRetrieveLevel = "SERIES"
            ds.SeriesInstanceUID = series_instance_uid
        else:
            ds.QueryRetrieveLevel = "STUDY"
        ds.StudyInstanceUID = study_instance_uid

        try:
            handlers = [(evt.EVT_C_STORE, handle_store)]
            assoc = ae.associate(
                self.host,
                self.port,
                ae_title=self.ae_title,
                evt_handlers=handlers
            )

            if assoc.is_established:
                if use_get:
                    responses = assoc.send_c_get(
                        ds,
                        StudyRootQueryRetrieveInformationModelGet
                    )
                else:
                    if not move_destination:
                        move_destination = self.local_ae_title
                    responses = assoc.send_c_move(
                        ds,
                        move_destination,
                        StudyRootQueryRetrieveInformationModelMove
                    )

                for status, identifier in responses:
                    if status:
                        if status.Status not in (0x0000, 0xFF00, 0xFF01):
                            errors.append(f"Status: {hex(status.Status)}")

                assoc.release()

                return {
                    "success": len(received_files) > 0,
                    "received_count": len(received_files),
                    "files": received_files,
                    "errors": errors
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to establish association",
                    "errors": ["Association rejected"]
                }

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "errors": [str(e)]
            }


def get_dicom_service(server_config: Dict[str, Any]) -> DicomService:
    """Factory function to create DicomService from server config"""
    return DicomService(
        ae_title=server_config["ae_title"],
        host=server_config["host"],
        port=server_config["port"],
        local_ae_title=server_config.get(
            "local_ae_title",
            get_cached_setting("dicom.local_ae_title", settings.DICOM_AE_TITLE)
        )
    )
