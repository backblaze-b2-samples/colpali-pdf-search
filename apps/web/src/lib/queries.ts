"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  deleteDocument,
  deleteFile,
  getCorpusStats,
  getDocument,
  getDocuments,
  getFileDetail,
  getFiles,
  getFileStats,
  getHealth,
  getPreviewUrl,
  getUploadActivity,
  indexDocument,
  renameDocument,
  visualSearch,
} from "@/lib/api-client";
import type {
  Document,
  DocumentDetail,
  FileMetadata,
  FileMetadataDetail,
  SearchResponse,
} from "@colpali-pdf-search/shared";

// Single source of truth for query keys. Keep these tightly scoped so that
// invalidating "files" doesn't blow away unrelated caches, and so an IDE
// "find usages" of `qk.files` reveals every consumer.
export const qk = {
  all: ["b2"] as const,
  files: (prefix?: string, limit?: number) =>
    [...qk.all, "files", prefix ?? "", limit ?? 100] as const,
  stats: () => [...qk.all, "stats"] as const,
  uploadActivity: (days: number) =>
    [...qk.all, "stats", "activity", days] as const,
  preview: (key: string) => [...qk.all, "preview", key] as const,
  detail: (key: string) => [...qk.all, "detail", key] as const,
  health: () => [...qk.all, "health"] as const,
  documents: () => [...qk.all, "documents"] as const,
  document: (id: string) => [...qk.all, "documents", id] as const,
  corpusStats: () => [...qk.all, "corpus-stats"] as const,
  search: (query: string, topK: number) =>
    [...qk.all, "search", query, topK] as const,
};

export type Health = Awaited<ReturnType<typeof getHealth>>;

export function useFiles(prefix = "", limit = 100) {
  return useQuery<FileMetadata[], ApiError>({
    queryKey: qk.files(prefix, limit),
    queryFn: () => getFiles(prefix, limit),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: qk.stats(),
    queryFn: getFileStats,
  });
}

export function useUploadActivity(days = 7) {
  return useQuery({
    queryKey: qk.uploadActivity(days),
    queryFn: () => getUploadActivity(days),
  });
}

// Presigned preview URL — only fetched when `enabled` is true (e.g., when
// the dialog opens for a specific file). Kept short-lived (60s) because
// the URL itself has a presigned expiry and is cheap to regenerate.
export function usePreviewUrl(key: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.preview(key ?? ""),
    queryFn: () => getPreviewUrl(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

// Rich metadata for an already-stored file. The server recomputes it on demand
// (a full object download), so it's only fetched when `enabled` — i.e. the
// preview dialog is open AND the user expands "Detailed metadata". Kept
// short-lived like the preview URL; cheap correctness under key overwrites.
export function useFileDetail(key: string | undefined, enabled: boolean) {
  return useQuery<FileMetadataDetail, ApiError>({
    queryKey: qk.detail(key ?? ""),
    queryFn: () => getFileDetail(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

// Health poll for the top-of-app B2 banner. `retry: false` and letting a
// failed fetch leave `data` undefined keeps a down API silent (the
// per-component ErrorState covers that); the banner only reacts to an up API
// reporting b2_connected: false. Polls every 60s and on window focus.
export function useHealth() {
  return useQuery<Health>({
    queryKey: qk.health(),
    queryFn: getHealth,
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: false,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileKey: string) => deleteFile(fileKey),
    // After delete, blow away every cached file list + stats. Cheap and
    // correct — the dashboard re-fetches lazily as components remount.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

// --- Documents (ColPali corpus) -------------------------------------------

export function useDocuments() {
  return useQuery<Document[], ApiError>({
    queryKey: qk.documents(),
    queryFn: getDocuments,
  });
}

export function useCorpusStats() {
  return useQuery({
    queryKey: qk.corpusStats(),
    queryFn: getCorpusStats,
  });
}

export function useDocument(id: string | undefined) {
  return useQuery<DocumentDetail, ApiError>({
    queryKey: qk.document(id ?? ""),
    queryFn: () => getDocument(id as string),
    enabled: !!id,
  });
}

export function useRenameDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      renameDocument(id, title),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.all }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.all }),
  });
}

/** Kick off ColPali embedding + FAISS (re)build for one document. */
export function useIndexDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => indexDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.all }),
  });
}

// --- Visual search --------------------------------------------------------

// Fetches only when `query` is non-empty. The submitted query is part of the
// key so results cache per query and don't refetch while the box is edited.
export function useVisualSearch(query: string, topK = 10) {
  return useQuery<SearchResponse, ApiError>({
    queryKey: qk.search(query, topK),
    queryFn: () => visualSearch(query, topK),
    enabled: query.trim().length > 0,
    staleTime: 60_000,
  });
}
