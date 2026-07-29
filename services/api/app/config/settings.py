from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Backblaze B2, S3-compatible API. Standard B2_* names (see .env.example).
    # The S3 endpoint is derived from the region, so no full endpoint URL is
    # stored and no region string is hardcoded in source.
    b2_application_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = ""
    b2_region: str = ""
    b2_public_url_base: str = ""

    # ColPali visual-embedding model. Runs locally — no external provider key.
    # Default base (PaliGemma) is HF-gated: a one-time free HF account + accepting
    # the model terms is needed to download weights. The colqwen2 alternative is
    # ungated and lighter. HF_TOKEN is a model-download token, NOT a per-run key.
    colpali_model: str = "vidore/colpali-v1.2"
    # Empty = runtime autodetect (CUDA -> CPU; MPS skipped by default, see
    # repo/colpali.py). Override with "cuda", "mps", or "cpu".
    colpali_device: str = ""
    hf_token: str = ""
    # Rendered page resolution. Finite set surfaced in the ingest form.
    render_dpi: int = 150
    # How many nearest pages a visual search returns.
    search_top_k: int = 10

    api_port: int = 8000
    # Interactive API docs (/docs, /redoc, /openapi.json). On by default for
    # local dev and starter-kit exploration; set false to hide the full API
    # surface in production.
    enable_docs: bool = True
    # Explicit allowlist by default — covers Next on :3000 and the
    # fallback :3001 it picks if 3000 is busy. Production deploys should
    # override with the exact frontend origin.
    api_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    # Optional dev-only escape hatch: a regex that matches additional
    # allowed origins. Empty by default — set this to e.g.
    # `^http://localhost:\d+$` to accept any localhost port without
    # listing each one. NEVER ship this to production.
    api_cors_origin_regex: str = ""

    # Upload limits
    max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Optional confinement for key-addressed reads/deletes. Empty by default so
    # the by-key routes accept any key shape (they deliberately support nested
    # folders and reserved-word segments). Point a fork at a bucket shared with
    # other data? Set to e.g. "uploads/" to restrict all key ops to app uploads.
    allowed_key_prefix: str = ""

    # Rate limiting (per client IP, per 60s window). In-process per replica —
    # documented in docs/RELIABILITY.md; horizontal scaling needs a shared
    # store (e.g. Redis). Writes/downloads get the tighter cap.
    rate_limit_per_minute: int = 120
    # Covers uploads, deletes, downloads and previews — kept generous enough
    # that a normal browsing/upload session doesn't trip it.
    rate_limit_write_per_minute: int = 60

    # Small durable counters (downloads, etc). Point at a persistent
    # volume in production if you care about surviving restarts.
    download_count_file: str = "data/download_count.json"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def b2_endpoint(self) -> str:
        """S3 endpoint derived from the region. Empty when region is unset so
        startup validation surfaces the missing B2_REGION rather than building
        a malformed URL."""
        if not self.b2_region:
            return ""
        return f"https://s3.{self.b2_region}.backblazeb2.com"

    @property
    def cors_origins(self) -> list[str]:
        # Drop empties so a trailing comma or API_CORS_ORIGINS="" doesn't yield
        # a stray "" origin.
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


settings = Settings()
