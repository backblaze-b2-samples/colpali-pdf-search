import Link from "next/link";
import { Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { CorpusStats } from "@/components/dashboard/corpus-stats";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Your visual-search corpus, stored end-to-end in Backblaze B2.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild size="sm" variant="outline" className="h-8">
            <Link href="/search">
              <Search className="h-3.5 w-3.5" />
              Search
            </Link>
          </Button>
          <Button asChild size="sm" className="h-8">
            <Link href="/ingest">
              <Plus className="h-3.5 w-3.5" />
              Ingest PDF
            </Link>
          </Button>
        </div>
      </div>
      <CorpusStats />
    </div>
  );
}
