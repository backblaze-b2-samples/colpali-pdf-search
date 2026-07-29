import { IngestForm } from "@/components/ingest/ingest-form";

export default function IngestPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Ingest</h1>
        <p className="mt-1.5 max-w-prose text-sm text-muted-foreground text-pretty">
          Upload a PDF. Every page is rendered to an image and stored in
          Backblaze B2, ready to embed with ColPali and search visually.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2 max-w-3xl">
        <IngestForm />
      </div>
    </div>
  );
}
