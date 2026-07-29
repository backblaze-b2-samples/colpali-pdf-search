import os

# faiss-cpu and PyTorch each bundle their own OpenMP runtime. Loading both into
# one process trips OpenMP's duplicate-runtime guard, which calls abort()
# ("OMP: Error #15") the first time FAISS runs a search after torch is loaded —
# crashing the API mid-query. Allowing the duplicate is Intel's documented,
# safe-for-CPU-inference workaround. Set here because this package initializes
# before either heavy repo module (colpali -> torch, faiss_index -> faiss) is
# imported, so the variable is in the environment before any OpenMP runtime loads.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from app.repo.b2_client import (
    check_connectivity,
    delete_file,
    get_file_metadata,
    get_presigned_url,
    get_upload_stats,
    list_files,
    upload_file,
)
from app.repo.b2_object import get_object_bytes
from app.repo.counter import get_download_count, increment_download_count

__all__ = [
    "check_connectivity",
    "delete_file",
    "get_download_count",
    "get_file_metadata",
    "get_object_bytes",
    "get_presigned_url",
    "get_upload_stats",
    "increment_download_count",
    "list_files",
    "upload_file",
]
