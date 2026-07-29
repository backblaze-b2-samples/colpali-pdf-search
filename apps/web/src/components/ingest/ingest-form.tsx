"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { FileText, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { ingestDocument } from "@/lib/api-client";
import { useQueryClient } from "@tanstack/react-query";
import { qk } from "@/lib/queries";

// dpi and model are finite option sets -> Select (never free text). Title is
// open-ended -> plain input with a safe-default hint (placeholder only, no
// autofill button).
const ingestSchema = z.object({
  title: z.string().max(120, "Keep the title under 120 characters").optional(),
  dpi: z.enum(["72", "100", "150"]),
  model: z.enum(["vidore/colpali-v1.2", "vidore/colqwen2-v1.0"]),
});

type IngestValues = z.infer<typeof ingestSchema>;

const defaultValues: IngestValues = {
  title: "",
  dpi: "150",
  model: "vidore/colpali-v1.2",
};

export function IngestForm() {
  const router = useRouter();
  const qc = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState<number | null>(null);

  const form = useForm<IngestValues>({
    resolver: zodResolver(ingestSchema),
    defaultValues,
  });

  const onSubmit = async (values: IngestValues) => {
    if (!file) {
      toast.error("Choose a PDF to ingest first.");
      return;
    }
    setProgress(0);
    try {
      const doc = await ingestDocument(
        file,
        { title: values.title ?? "", dpi: values.dpi, model: values.model },
        (percent) => setProgress(percent)
      );
      qc.invalidateQueries({ queryKey: qk.all });
      toast.success(`"${doc.title}" ingested — ${doc.page_count} pages rendered.`);
      router.push(`/documents/${doc.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ingest failed";
      toast.error(message);
      setProgress(null);
    }
  };

  const submitting = progress !== null;

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader className="border-b border-border py-4 px-5">
            <CardTitle className="card-title">Ingest a PDF</CardTitle>
          </CardHeader>
          <CardContent className="p-5 space-y-6">
            <div className="space-y-2">
              <FormLabel htmlFor="pdf">PDF document</FormLabel>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex w-full items-center gap-3 rounded-md border border-dashed border-border bg-muted/20 px-4 py-6 text-left transition-colors hover:bg-muted/40"
              >
                <FileText className="h-5 w-5 text-muted-foreground" />
                <span className="text-sm">
                  {file ? file.name : "Click to choose a PDF (max 100 MB)"}
                </span>
              </button>
              <input
                id="pdf"
                ref={fileInputRef}
                type="file"
                accept="application/pdf,.pdf"
                className="sr-only"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <p className="text-sm text-muted-foreground">
                Each page is rendered to an image and searched visually — no OCR.
              </p>
            </div>

            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input placeholder="Q3 Financial Report" {...field} />
                  </FormControl>
                  <FormDescription>
                    A human-friendly name for the document. Defaults to the file
                    name if left blank.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="dpi"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Render resolution (dpi)</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-60">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="72">72 dpi — smallest / fastest</SelectItem>
                      <SelectItem value="100">100 dpi — balanced</SelectItem>
                      <SelectItem value="150">150 dpi — sharp thumbnails</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    150 dpi gives sharp page thumbnails; lower dpi renders
                    smaller, faster, and stores fewer bytes in B2.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>ColPali model</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-72">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="vidore/colpali-v1.2">
                        vidore/colpali-v1.2 (PaliGemma)
                      </SelectItem>
                      <SelectItem value="vidore/colqwen2-v1.0">
                        vidore/colqwen2-v1.0 (ungated, lighter)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    colpali-v1.2 is the default; its PaliGemma base is HF-gated.
                    colqwen2-v1.0 needs no Hugging Face token and is lighter.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {progress !== null && (
              <div className="space-y-1.5">
                <Progress value={progress} />
                <p className="text-xs text-muted-foreground">
                  Uploading and rendering pages… {progress}%
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-2">
          <Button type="submit" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Ingesting…
              </>
            ) : (
              "Ingest document"
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}
