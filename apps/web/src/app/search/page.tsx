import { VisualSearch } from "@/components/search/visual-search";

export default function SearchPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Visual Search</h1>
        <p className="mt-1.5 max-w-prose text-sm text-muted-foreground text-pretty">
          Type a natural-language query and land on the exact page. Retrieval
          runs over ColPali page embeddings stored in Backblaze B2.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <VisualSearch />
      </div>
    </div>
  );
}
