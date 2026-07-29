"use client";

import Link from "next/link";
import { FileText, Library } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useDocuments } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

function StatusBadge({ status }: { status: string }) {
  const indexed = status === "indexed";
  return (
    <Badge variant={indexed ? "default" : "secondary"}>
      {indexed ? "Indexed" : "Rendered"}
    </Badge>
  );
}

export function DocumentLibrary() {
  const { data: documents = [], isLoading, error, refetch } = useDocuments();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }

  if (documents.length === 0) {
    return (
      <EmptyState
        icon={Library}
        title="No documents yet"
        description="Head to Ingest to add your first PDF to the corpus."
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {documents.map((doc) => (
        <Link key={doc.id} href={`/documents/${doc.id}`} className="group">
          <Card className="card-hover overflow-hidden h-full">
            <div className="flex h-40 items-center justify-center overflow-hidden border-b border-border bg-muted/30">
              {doc.thumbnail_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={doc.thumbnail_url}
                  alt={`Page 1 of ${doc.title}`}
                  className="h-full w-full object-contain"
                />
              ) : (
                <FileText className="h-10 w-10 text-muted-foreground" />
              )}
            </div>
            <CardContent className="space-y-2 p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="truncate font-medium group-hover:text-primary">
                  {doc.title}
                </h3>
                <StatusBadge status={doc.status} />
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span>{doc.page_count} pages</span>
                <span>{doc.dpi} dpi</span>
                <span className="truncate">{doc.model}</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Added {formatDate(doc.created_at)}
              </p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
