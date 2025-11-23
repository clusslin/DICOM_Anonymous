"""
DICOM Anonymization Service
Handles the anonymization of DICOM files while preserving image data and transfer syntax
"""
import os
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
from pydicom.tag import Tag

from app.models.anonymization_config import DEFAULT_ANONYMIZATION_TAGS
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnonymizationService:
    """Service for anonymizing DICOM files"""

    # DICOM tags that should be handled specially
    UID_TAGS = [
        "StudyInstanceUID",
        "SeriesInstanceUID",
        "SOPInstanceUID",
        "FrameOfReferenceUID",
        "ReferencedSOPInstanceUID",
        "RelatedFrameOfReferenceUID"
    ]

    def __init__(
        self,
        new_patient_id: str = None,
        new_patient_name: str = None,
        anonymization_options: Dict[str, Dict[str, str]] = None,
        uid_mapping: Dict[str, str] = None
    ):
        """
        Initialize the anonymization service

        Args:
            new_patient_id: New patient ID to use (or generate if None)
            new_patient_name: New patient name to use (or use default)
            anonymization_options: Custom options for tag handling
            uid_mapping: Existing UID mappings to maintain consistency
        """
        self.new_patient_id = new_patient_id or self._generate_anonymous_id()
        self.new_patient_name = new_patient_name or settings.DEFAULT_REPLACEMENT_NAME

        # Merge default options with custom options
        self.options = DEFAULT_ANONYMIZATION_TAGS.copy()
        if anonymization_options:
            self.options.update(anonymization_options)

        # UID mapping to maintain referential integrity
        self.uid_mapping = uid_mapping or {}

        # Hash salt for consistent hashing
        self.hash_salt = str(uuid.uuid4())

    def _generate_anonymous_id(self) -> str:
        """Generate a random anonymous patient ID"""
        return f"ANON{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    def _hash_value(self, value: str) -> str:
        """Create a consistent hash of a value"""
        combined = f"{self.hash_salt}{value}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16].upper()

    def _generate_new_uid(self, original_uid: str) -> str:
        """Generate a new UID while maintaining mapping for consistency"""
        if original_uid in self.uid_mapping:
            return self.uid_mapping[original_uid]

        new_uid = generate_uid()
        self.uid_mapping[original_uid] = new_uid
        return new_uid

    def _process_tag(self, ds: Dataset, tag_name: str, action: str, replacement_value: str = None) -> None:
        """Process a single DICOM tag based on the action"""
        if tag_name not in ds:
            return

        if action == "remove":
            del ds[tag_name]

        elif action == "replace":
            if tag_name == "PatientName":
                ds.PatientName = self.new_patient_name
            elif tag_name == "PatientID":
                ds.PatientID = self.new_patient_id
            elif replacement_value:
                setattr(ds, tag_name, replacement_value)
            else:
                setattr(ds, tag_name, "")

        elif action == "hash":
            if tag_name in self.UID_TAGS:
                original_value = str(getattr(ds, tag_name))
                new_value = self._generate_new_uid(original_value)
                setattr(ds, tag_name, new_value)
            else:
                original_value = str(getattr(ds, tag_name))
                setattr(ds, tag_name, self._hash_value(original_value))

        elif action == "keep":
            pass  # Do nothing, keep the original value

    def _remove_private_tags(self, ds: Dataset) -> None:
        """Remove all private tags from the dataset"""
        private_tags = [tag for tag in ds if tag.is_private]
        for tag in private_tags:
            del ds[tag]

    def _handle_sequences(self, ds: Dataset) -> None:
        """Recursively handle sequences in the dataset"""
        for elem in ds:
            if elem.VR == "SQ":
                for item in elem.value:
                    self.anonymize_dataset(item)

    def anonymize_dataset(self, ds: Dataset) -> Dataset:
        """
        Anonymize a DICOM dataset in place

        Args:
            ds: The DICOM dataset to anonymize

        Returns:
            The anonymized dataset
        """
        # Process each configured tag
        for tag_name, config in self.options.items():
            if tag_name == "PrivateTags":
                if config.get("action") == "remove":
                    self._remove_private_tags(ds)
                continue

            action = config.get("action", "keep")
            replacement = config.get("value")
            self._process_tag(ds, tag_name, action, replacement)

        # Handle sequences recursively
        self._handle_sequences(ds)

        return ds

    def anonymize_file(
        self,
        input_path: str,
        output_path: str,
        preserve_transfer_syntax: bool = True
    ) -> Dict[str, Any]:
        """
        Anonymize a DICOM file

        Args:
            input_path: Path to the input DICOM file
            output_path: Path for the output anonymized file
            preserve_transfer_syntax: If True, preserve the original transfer syntax (e.g., JPEG2000)

        Returns:
            Dictionary with result information
        """
        try:
            # Read the DICOM file
            ds = dcmread(input_path)

            # Store original transfer syntax
            original_transfer_syntax = ds.file_meta.TransferSyntaxUID

            # Anonymize the dataset
            self.anonymize_dataset(ds)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if preserve_transfer_syntax:
                # Save with original transfer syntax (don't decompress JPEG2000)
                ds.save_as(output_path, write_like_original=True)
            else:
                # Save with default transfer syntax
                ds.save_as(output_path)

            return {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "original_transfer_syntax": str(original_transfer_syntax),
                "new_patient_id": self.new_patient_id,
                "new_patient_name": self.new_patient_name
            }

        except Exception as e:
            logger.error(f"Failed to anonymize file {input_path}: {e}")
            return {
                "success": False,
                "input_path": input_path,
                "error": str(e)
            }

    def anonymize_directory(
        self,
        input_dir: str,
        output_dir: str,
        preserve_transfer_syntax: bool = True
    ) -> Dict[str, Any]:
        """
        Anonymize all DICOM files in a directory

        Args:
            input_dir: Path to input directory containing DICOM files
            output_dir: Path for output directory
            preserve_transfer_syntax: If True, preserve original transfer syntax

        Returns:
            Dictionary with processing statistics
        """
        results = {
            "success": True,
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "files": [],
            "errors": []
        }

        # Find all DICOM files
        dicom_files = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.dcm') or '.' not in file:
                    dicom_files.append(os.path.join(root, file))

        results["total_files"] = len(dicom_files)

        # Process each file
        for input_path in dicom_files:
            # Generate output path
            rel_path = os.path.relpath(input_path, input_dir)
            output_path = os.path.join(output_dir, rel_path)

            result = self.anonymize_file(input_path, output_path, preserve_transfer_syntax)

            if result["success"]:
                results["processed_files"] += 1
                results["files"].append(result)
            else:
                results["failed_files"] += 1
                results["errors"].append(result)

        results["success"] = results["failed_files"] == 0

        return results

    def get_uid_mapping(self) -> Dict[str, str]:
        """Get the UID mapping for maintaining referential integrity"""
        return self.uid_mapping.copy()


def create_anonymization_service(
    new_patient_id: str = None,
    new_patient_name: str = None,
    options: Dict[str, Dict[str, str]] = None
) -> AnonymizationService:
    """Factory function to create AnonymizationService"""
    return AnonymizationService(
        new_patient_id=new_patient_id,
        new_patient_name=new_patient_name,
        anonymization_options=options
    )
