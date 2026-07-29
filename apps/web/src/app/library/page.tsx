import Link from "next/link";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DocumentLibrary } from "@/components/library/document-library";

export default function LibraryPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in flex flex-wrap items-start justify-between gap-4 border-b border-border pb-5">
        <div className="min-w-0">
          <h1 className="page-title">Library</h1>
          <p className="mt-1.5 max-w-prose text-sm text-muted-foreground">
            Your ingested documents, scoped to this app&apos;s{" "}
            <code className="text-xs">documents/</code> prefix in B2.
          </p>
        </div>
        <Button asChild size="sm" className="h-8 shrink-0">
          <Link href="/ingest">
            <Plus aria-hidden="true" className="h-3.5 w-3.5" />
            Ingest PDF
          </Link>
        </Button>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <DocumentLibrary />
      </div>
    </div>
  );
}
