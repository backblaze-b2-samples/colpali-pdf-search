export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Image-specific
  image_width: number | null;
  image_height: number | null;
  exif: Record<string, string> | null;
  // PDF-specific
  pdf_pages: number | null;
  pdf_author: string | null;
  pdf_title: string | null;
  // Audio/Video
  duration_seconds: number | null;
  codec: string | null;
  bitrate: number | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export type DocumentStatus = "rendered" | "indexing" | "indexed";

export interface Document {
  id: string;
  title: string;
  page_count: number;
  dpi: number;
  model: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
  page_bytes: number;
  embedding_bytes: number;
  // Pages embedded so far while status === "indexing" (0..page_count).
  pages_indexed: number;
  thumbnail_url: string | null;
}

export interface DocumentPage {
  page: number;
  key: string;
  url: string;
}

export interface DocumentDetail extends Document {
  pages: DocumentPage[];
}

export interface CorpusStats {
  documents: number;
  indexed_documents: number;
  total_pages: number;
  page_bytes: number;
  page_bytes_human: string;
  embedding_bytes: number;
  embedding_bytes_human: string;
  index_bytes: number;
  index_bytes_human: string;
}

export interface SearchHit {
  doc_id: string;
  title: string;
  page: number;
  score: number;
  key: string;
  url: string;
}

export interface SearchResponse {
  query: string;
  top_k: number;
  hits: SearchHit[];
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
}
