import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import logging

logger = logging.getLogger(__name__)

class DocumentIngester:
    def __init__(self, max_size_mb=50):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_extensions = {'.pdf', '.txt', '.md'}

    def ingest_bytes(self, file_bytes: bytes, filename: str, project_id=1, source_type="user_upload") -> list[dict]:
        """Ingest document directly from memory bytes without creating temporary disk files."""
        if not file_bytes:
            logger.error(f"File is empty (0 bytes): {filename}")
            return []

        if len(file_bytes) > self.max_size_bytes:
            logger.error(f"File too large: {filename} ({len(file_bytes)} bytes)")
            return []

        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            logger.error(f"Unsupported file type: {ext}")
            return []

        try:
            if ext == '.pdf':
                return self._ingest_pdf_bytes(file_bytes, filename, project_id, source_type)
            elif ext == '.txt':
                return self._ingest_txt_bytes(file_bytes, filename, project_id, source_type)
            elif ext == '.md':
                return self._ingest_md_bytes(file_bytes, filename, project_id, source_type)
        except Exception as e:
            logger.error(f"Extraction failed for memory bytes of {filename}: {e}")
            return []
        return []

    def _ingest_pdf_bytes(self, file_bytes: bytes, filename: str, project_id, source_type) -> list[dict]:
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
        except ImportError:
            logger.error("PyMuPDF is not installed.")
            return []

        chunks = []
        doc = None
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    chunks.append({
                        "text": text,
                        "metadata": {
                            "document_name": filename,
                            "page_number": page_num + 1,
                            "section": "",
                            "document_type": "pdf",
                            "project_id": project_id,
                            "source_type": source_type
                        }
                    })
        finally:
            if doc:
                doc.close()
        return chunks

    def _ingest_txt_bytes(self, file_bytes: bytes, filename: str, project_id, source_type) -> list[dict]:
        text = file_bytes.decode('utf-8', errors='ignore')
        if not text.strip():
            return []
        return [{
            "text": text,
            "metadata": {
                "document_name": filename,
                "page_number": 1,
                "section": "",
                "document_type": "txt",
                "project_id": project_id,
                "source_type": source_type
            }
        }]

    def _ingest_md_bytes(self, file_bytes: bytes, filename: str, project_id, source_type) -> list[dict]:
        text = file_bytes.decode('utf-8', errors='ignore')
        if not text.strip():
            return []
        lines = text.splitlines(keepends=True)
        chunks = []
        current_section = ""
        current_text = []

        for line in lines:
            if line.startswith('#'):
                if current_text:
                    chunks.append({
                        "text": "".join(current_text),
                        "metadata": {
                            "document_name": filename,
                            "page_number": 1,
                            "section": current_section,
                            "document_type": "md",
                            "project_id": project_id,
                            "source_type": source_type
                        }
                    })
                    current_text = []
                current_section = line.strip('# \n')
            current_text.append(line)

        if current_text:
            chunks.append({
                "text": "".join(current_text),
                "metadata": {
                    "document_name": filename,
                    "page_number": 1,
                    "section": current_section,
                    "document_type": "md",
                    "project_id": project_id,
                    "source_type": source_type
                }
            })

        return chunks

    def ingest_file(self, file_path, project_id=1, source_type="user_upload", original_filename=None) -> list[dict]:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []
            
        if path.stat().st_size > self.max_size_bytes:
            logger.error(f"File too large: {file_path}")
            return []
            
        ext = path.suffix.lower()
        if ext not in self.allowed_extensions:
            logger.error(f"Unsupported file type: {ext}")
            return []
            
        doc_name = original_filename if original_filename else path.name

        try:
            if ext == '.pdf':
                return self._ingest_pdf(path, project_id, source_type, doc_name=doc_name)
            elif ext == '.txt':
                return self._ingest_txt(path, project_id, source_type, doc_name=doc_name)
            elif ext == '.md':
                return self._ingest_md(path, project_id, source_type, doc_name=doc_name)
        except Exception as e:
            logger.error(f"Extraction failed for {file_path}: {e}")
            return []
        return []

    def _ingest_pdf(self, path: Path, project_id, source_type, doc_name=None) -> list[dict]:
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
        except ImportError:
            logger.error("PyMuPDF is not installed.")
            return []
            
        chunks = []
        doc = None
        name = doc_name if doc_name else path.name
        try:
            doc = fitz.open(str(path))
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    chunks.append({
                        "text": text,
                        "metadata": {
                            "document_name": name,
                            "page_number": page_num + 1,
                            "section": "",
                            "document_type": "pdf",
                            "project_id": project_id,
                            "source_type": source_type
                        }
                    })
        finally:
            if doc:
                doc.close()
        return chunks

    def _ingest_txt(self, path: Path, project_id, source_type, doc_name=None) -> list[dict]:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        name = doc_name if doc_name else path.name
        if not text.strip():
            return []
        return [{
            "text": text,
            "metadata": {
                "document_name": name,
                "page_number": 1,
                "section": "",
                "document_type": "txt",
                "project_id": project_id,
                "source_type": source_type
            }
        }]

    def _ingest_md(self, path: Path, project_id, source_type, doc_name=None) -> list[dict]:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        chunks = []
        name = doc_name if doc_name else path.name
        current_section = ""
        current_text = []
        
        for line in lines:
            if line.startswith('#'):
                if current_text:
                    chunks.append({
                        "text": "".join(current_text),
                        "metadata": {
                            "document_name": name,
                            "page_number": 1,
                            "section": current_section,
                            "document_type": "md",
                            "project_id": project_id,
                            "source_type": source_type
                        }
                    })
                    current_text = []
                current_section = line.strip('# \n')
            current_text.append(line)
            
        if current_text:
            chunks.append({
                "text": "".join(current_text),
                "metadata": {
                    "document_name": name,
                    "page_number": 1,
                    "section": current_section,
                    "document_type": "md",
                    "project_id": project_id,
                    "source_type": source_type
                }
            })
            
        return chunks

    def ingest_directory(self, dir_path, project_id, source_type) -> list[dict]:
        all_chunks = []
        path = Path(dir_path)
        if not path.is_dir():
            logger.error(f"Directory not found: {dir_path}")
            return []
            
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                all_chunks.extend(self.ingest_file(file_path, project_id, source_type))
        return all_chunks
