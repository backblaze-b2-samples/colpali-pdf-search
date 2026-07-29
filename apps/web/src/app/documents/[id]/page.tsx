"use client";

import { useParams } from "next/navigation";

import { DocumentDetailView } from "@/components/documents/document-detail";

export default function DocumentPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  return (
    <div className="animate-fade-in">
      {id ? <DocumentDetailView id={id} /> : null}
    </div>
  );
}
