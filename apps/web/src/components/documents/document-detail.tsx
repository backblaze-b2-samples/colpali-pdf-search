"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Pencil, Play, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  useDeleteDocument,
  useDocument,
  useIndexDocument,
  useRenameDocument,
} from "@/lib/queries";
import { formatDate, humanizeBytes } from "@/lib/utils";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-0.5 text-sm font-medium tabular-nums">{value}</div>
    </div>
  );
}

export function DocumentDetailView({ id }: { id: string }) {
  const router = useRouter();
  const { data: doc, isLoading, error, refetch } = useDocument(id);
  const rename = useRenameDocument();
  const remove = useDeleteDocument();
  const runIndex = useIndexDocument();

  const [renameOpen, setRenameOpen] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");

  if (isLoading) return <Skeleton className="h-96 w-full" />;
  if (error) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!doc) return null;

  const indexed = doc.status === "indexed";

  const submitRename = () => {
    rename.mutate(
      { id: doc.id, title: titleDraft },
      {
        onSuccess: () => {
          toast.success("Document renamed");
          setRenameOpen(false);
        },
        onError: (e) => toast.error(e.message),
      }
    );
  };

  const submitDelete = () => {
    remove.mutate(doc.id, {
      onSuccess: () => {
        toast.success("Document deleted");
        router.push("/library");
      },
      onError: (e) => toast.error(e.message),
    });
  };

  const submitIndex = () => {
    runIndex.mutate(doc.id, {
      onSuccess: (d) =>
        toast.success(`Indexed — ${humanizeBytes(d.embedding_bytes)} of embeddings stored`),
      onError: (e) => toast.error(e.message),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-5">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <h1 className="page-title truncate">{doc.title}</h1>
            <Badge variant={indexed ? "default" : "secondary"}>
              {indexed ? "Indexed" : "Rendered"}
            </Badge>
          </div>
          <p className="mt-1.5 text-sm text-muted-foreground">
            {doc.page_count} pages · added {formatDate(doc.created_at)}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-8"
            onClick={() => {
              setTitleDraft(doc.title);
              setRenameOpen(true);
            }}
          >
            <Pencil className="h-3.5 w-3.5" />
            Rename
          </Button>
          <Button size="sm" className="h-8" onClick={submitIndex} disabled={runIndex.isPending}>
            {runIndex.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            {indexed ? "Re-index" : "Run indexing"}
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 text-destructive">
                <Trash2 className="h-3.5 w-3.5" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete this document?</AlertDialogTitle>
                <AlertDialogDescription>
                  Removes its page images, embeddings, and metadata from B2 and
                  rebuilds the search index. This cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={submitDelete} disabled={remove.isPending}>
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <Card>
        <CardContent className="grid grid-cols-2 gap-4 p-5 sm:grid-cols-3 lg:grid-cols-5">
          <Stat label="Pages" value={String(doc.page_count)} />
          <Stat label="Resolution" value={`${doc.dpi} dpi`} />
          <Stat label="Model" value={doc.model} />
          <Stat label="Page images" value={humanizeBytes(doc.page_bytes)} />
          <Stat label="Embeddings" value={humanizeBytes(doc.embedding_bytes)} />
        </CardContent>
      </Card>

      {runIndex.isPending && (
        <p className="text-sm text-muted-foreground">
          Embedding pages with ColPali and rebuilding the FAISS index… this can
          take a while on CPU.
        </p>
      )}

      <div>
        <h2 className="card-title mb-3">Pages</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {doc.pages.map((page) => (
            <figure key={page.key} className="overflow-hidden rounded-md border border-border">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={page.url}
                alt={`Page ${page.page}`}
                className="w-full bg-muted/30 object-contain"
              />
              <figcaption className="border-t border-border px-2 py-1 text-center text-xs text-muted-foreground">
                Page {page.page}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>

      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename document</DialogTitle>
          </DialogHeader>
          <Input
            value={titleDraft}
            onChange={(e) => setTitleDraft(e.target.value)}
            aria-label="Document title"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenameOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitRename} disabled={rename.isPending}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
