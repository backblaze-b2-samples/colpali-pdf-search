"use client";

import { FileText, Layers, Image as ImageIcon, Database } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useCorpusStats } from "@/lib/queries";

export function CorpusStats() {
  const { data: stats, isLoading, error, refetch } = useCorpusStats();

  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }

  const cards = [
    { title: "Documents", value: stats?.documents ?? 0, icon: FileText },
    { title: "Indexed", value: stats?.indexed_documents ?? 0, icon: Layers },
    { title: "Total Pages", value: stats?.total_pages ?? 0, icon: ImageIcon },
    { title: "Index Size", value: stats?.index_bytes_human ?? "0 B", icon: Database },
  ];

  // Write-amplification headline: one PDF explodes into many page images plus
  // per-page multi-vector embeddings that can rival the image footprint.
  const pageBytes = stats?.page_bytes ?? 0;
  const embeddingBytes = stats?.embedding_bytes ?? 0;
  const ratio =
    pageBytes > 0 ? (embeddingBytes / pageBytes).toFixed(2) : "0.00";

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card, i) => (
          <Card key={card.title} className={`card-hover animate-fade-in-up stagger-${i + 1}`}>
            <CardHeader className="flex flex-row items-center justify-between pt-4 pb-2 px-4 space-y-0">
              <CardTitle className="text-xs font-semibold text-muted-foreground">
                {card.title}
              </CardTitle>
              <div className="stat-icon-wrap">
                <card.icon className="h-4 w-4" />
              </div>
            </CardHeader>
            <CardContent className="pb-5 px-4">
              {isLoading ? (
                <Skeleton className="h-8 w-24" />
              ) : (
                <div className="stat-value">{card.value}</div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="border-b border-border py-4 px-5">
          <CardTitle className="card-title">
            Storage: the write-amplification story
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Page images in B2
            </div>
            <div className="mt-0.5 stat-value">
              {isLoading ? "—" : stats?.page_bytes_human}
            </div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Embeddings in B2
            </div>
            <div className="mt-0.5 stat-value">
              {isLoading ? "—" : stats?.embedding_bytes_human}
            </div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Embedding : image ratio
            </div>
            <div className="mt-0.5 stat-value">{isLoading ? "—" : `${ratio}×`}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
