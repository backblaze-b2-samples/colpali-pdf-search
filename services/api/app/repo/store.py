"""Generic B2/S3 object operations for the ColPali document corpus.

Kept separate from `b2_client.py` (the file-browser/upload adapter, at its
300-line ceiling) but reuses the same cached, custom-UA S3 client so boto3
stays confined to the repo/ layer and connections are pooled. All access is via
the S3-compatible API — no b2-native calls anywhere.
"""

import io
import json
from urllib.parse import quote

from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.repo.b2_client import get_s3_client
from app.repo.b2_object import get_object_bytes

# Re-export so the service layer imports every object op from one module.
__all__ = [
    "delete_prefix",
    "get_object_bytes",
    "list_prefix",
    "presign_get",
    "public_url",
    "put_bytes",
    "read_json",
    "write_json",
]


def put_bytes(key: str, data: bytes, content_type: str) -> int:
    """Upload raw bytes to `key`. Returns the byte count. Raises RuntimeError."""
    client = get_s3_client()
    try:
        client.put_object(
            Bucket=settings.b2_bucket_name,
            Key=key,
            Body=io.BytesIO(data),
            ContentType=content_type,
        )
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"B2 put_object failed for '{key}': {e}") from e
    return len(data)


def list_prefix(prefix: str) -> list[dict]:
    """List every object under `prefix` (paginated). Raises RuntimeError."""
    client = get_s3_client()
    contents: list[dict] = []
    kwargs: dict = {"Bucket": settings.b2_bucket_name, "Prefix": prefix, "MaxKeys": 1000}
    try:
        while True:
            response = client.list_objects_v2(**kwargs)
            contents.extend(response.get("Contents", []))
            if not response.get("IsTruncated"):
                break
            kwargs["ContinuationToken"] = response["NextContinuationToken"]
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"B2 list failed for '{prefix}': {e}") from e
    return contents


def read_json(key: str) -> dict | None:
    """Read and parse a JSON object. Returns None if the key does not exist."""
    client = get_s3_client()
    try:
        response = client.get_object(Bucket=settings.b2_bucket_name, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey"):
            return None
        raise RuntimeError(f"B2 get_object failed for '{key}': {e}") from e
    return json.loads(response["Body"].read())


def write_json(key: str, payload: dict) -> None:
    """Serialize `payload` and store it as an application/json object."""
    put_bytes(key, json.dumps(payload).encode("utf-8"), "application/json")


def delete_prefix(prefix: str) -> int:
    """Delete every object under `prefix`. Returns the count. Raises RuntimeError.

    Scoped deletes only — callers pass a document's own prefix, never "".
    """
    if not prefix:
        raise ValueError("delete_prefix requires a non-empty prefix")
    client = get_s3_client()
    objects = [{"Key": obj["Key"]} for obj in list_prefix(prefix)]
    if not objects:
        return 0
    try:
        for start in range(0, len(objects), 1000):
            client.delete_objects(
                Bucket=settings.b2_bucket_name,
                Delete={"Objects": objects[start : start + 1000]},
            )
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"B2 delete failed for '{prefix}': {e}") from e
    return len(objects)


def presign_get(key: str, expires_in: int = 600) -> str:
    """Presigned inline-view URL for streaming a page image to the browser."""
    client = get_s3_client()
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.b2_bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"B2 presign failed for '{key}': {e}") from e


def public_url(key: str) -> str | None:
    """Public URL when B2_PUBLIC_URL_BASE is set (public buckets only)."""
    if not settings.b2_public_url_base:
        return None
    return f"{settings.b2_public_url_base}/{quote(key, safe='/')}"
