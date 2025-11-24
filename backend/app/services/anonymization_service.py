"""
DICOM Anonymization Service
Handles the anonymization of DICOM files and decompression of JPEG2000 images
"""
import os
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
from pydicom.tag import Tag
from pydicom.pixel_data_handlers.util import convert_color_space

from app.models.anonymization_config import DEFAULT_ANONYMIZATION_TAGS
from app.core.config import settings

logger = logging.getLogger(__name__)

# JPEG2000 Transfer Syntax UIDs
JPEG2000_TRANSFER_SYNTAXES = [
    "1.2.840.10008.1.2.4.90",  # JPEG 2000 Image Compression (Lossless Only)
    "1.2.840.10008.1.2.4.91",  # JPEG 2000 Image Compression
]

# All compressed transfer syntaxes
COMPRESSED_TRANSFER_SYNTAXES = [
    "1.2.840.10008.1.2.4.50",  # JPEG Baseline
    "1.2.840.10008.1.2.4.51",  # JPEG Extended
    "1.2.840.10008.1.2.4.57",  # JPEG Lossless
    "1.2.840.10008.1.2.4.70",  # JPEG Lossless, First-Order Prediction
    "1.2.840.10008.1.2.4.80",  # JPEG-LS Lossless
    "1.2.840.10008.1.2.4.81",  # JPEG-LS Lossy
    "1.2.840.10008.1.2.4.90",  # JPEG 2000 Lossless
    "1.2.840.10008.1.2.4.91",  # JPEG 2000 Lossy
    "1.2.840.10008.1.2.5",     # RLE Lossless
]


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

    def _is_compressed(self, ds: Dataset) -> bool:
        """Check if the dataset uses a compressed transfer syntax"""
        if not hasattr(ds, 'file_meta') or not hasattr(ds.file_meta, 'TransferSyntaxUID'):
            return False
        return str(ds.file_meta.TransferSyntaxUID) in COMPRESSED_TRANSFER_SYNTAXES

    def _decompress_pixel_data(self, ds: Dataset) -> Dataset:
        """
        Decompress pixel data from JPEG2000 or other compressed formats to uncompressed

        Args:
            ds: The DICOM dataset with compressed pixel data

        Returns:
            Dataset with uncompressed pixel data
        """
        try:
            original_syntax = str(ds.file_meta.TransferSyntaxUID)

            # Check if compressed
            if original_syntax not in COMPRESSED_TRANSFER_SYNTAXES:
                logger.debug(f"File is not compressed, skipping decompression")
                return ds

            logger.info(f"Decompressing from transfer syntax: {original_syntax}")

            # Decompress the pixel data
            # This will decode JPEG2000/JPEG/RLE to raw pixel array
            ds.decompress()

            # Update the transfer syntax to Explicit VR Little Endian (uncompressed)
            ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

            logger.info(f"Successfully decompressed to Explicit VR Little Endian")

            return ds

        except Exception as e:
            logger.error(f"Failed to decompress pixel data: {e}")
            # If decompression fails, return original dataset
            return ds

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
        decompress: bool = True
    ) -> Dict[str, Any]:
        """
        Anonymize a DICOM file and optionally decompress JPEG2000

        Args:
            input_path: Path to the input DICOM file
            output_path: Path for the output anonymized file
            decompress: If True, decompress JPEG2000/compressed images to uncompressed format

        Returns:
            Dictionary with result information
        """
        try:
            # Read the DICOM file
            ds = dcmread(input_path)

            # Store original transfer syntax
            original_transfer_syntax = str(ds.file_meta.TransferSyntaxUID)
            was_compressed = self._is_compressed(ds)

            # Decompress if needed
            if decompress and was_compressed:
                ds = self._decompress_pixel_data(ds)

            # Anonymize the dataset
            self.anonymize_dataset(ds)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save the file
            ds.save_as(output_path, write_like_original=False)

            return {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "original_transfer_syntax": original_transfer_syntax,
                "was_compressed": was_compressed,
                "decompressed": decompress and was_compressed,
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
        decompress: bool = True
    ) -> Dict[str, Any]:
        """
        Anonymize all DICOM files in a directory

        Args:
            input_dir: Path to input directory containing DICOM files
            output_dir: Path for output directory
            decompress: If True, decompress JPEG2000/compressed images

        Returns:
            Dictionary with processing statistics
        """
        results = {
            "success": True,
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "decompressed_files": 0,
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

            result = self.anonymize_file(input_path, output_path, decompress)

            if result["success"]:
                results["processed_files"] += 1
                if result.get("decompressed"):
                    results["decompressed_files"] += 1
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
