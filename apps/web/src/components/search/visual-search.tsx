"use client";

import { useState } from "react";
import Link from "next/link";
import { Search as SearchIcon, ImageOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useVisualSearch } from "@/lib/queries";

export function VisualSearch() {
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const { data, isLoading, error, refetch, isFetching } = useVisualSearch(query, 12);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setQuery(draft.trim());
  };

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="e.g. the slide with the revenue waterfall chart"
            className="pl-9"
            aria-label="Visual search query"
          />
        </div>
        <Button type="submit" disabled={draft.trim().length === 0 || isFetching}>
          Search
        </Button>
      </form>

      {query.length === 0 ? (
        <EmptyState
          icon={SearchIcon}
          title="Search your documents visually"
          description="Describe the page you're looking for. ColPali matches your words against page images — no OCR."
        />
      ) : isLoading ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : (data?.hits.length ?? 0) === 0 ? (
        <EmptyState
          icon={ImageOff}
          title="No matching pages"
          description="Nothing indexed yet, or no page matched. Ingest and index a document first."
        />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {data?.hits.map((hit) => (
            <Link key={hit.key} href={`/documents/${hit.doc_id}`} className="group">
              <Card className="card-hover overflow-hidden h-full">
                <div className="flex h-48 items-center justify-center overflow-hidden border-b border-border bg-muted/30">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={hit.url}
                    alt={`${hit.title} — page ${hit.page}`}
                    className="h-full w-full object-contain"
                  />
                </div>
                <CardContent className="space-y-1.5 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium group-hover:text-primary">
                      {hit.title}
                    </span>
                    <Badge variant="secondary">{hit.score.toFixed(2)}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">Page {hit.page}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
