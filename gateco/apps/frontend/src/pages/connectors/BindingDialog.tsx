import { useState, useCallback } from 'react';
import { Upload, AlertTriangle, CheckCircle2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useBindMetadata } from '@/hooks/useConnectors';
import type { BindingEntry } from '@/types/binding';
import type { BindResult } from '@/types/binding';

const MAX_BATCH_SIZE = 5000;
const REQUIRED_COLUMNS = ['vector_id', 'external_resource_id'];
const OPTIONAL_COLUMNS = ['classification', 'sensitivity', 'domain', 'labels'];

interface BindingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  connectorId: string;
  connectorName: string;
}

interface ValidationResult {
  valid: boolean;
  entries: BindingEntry[];
  warnings: string[];
  errors: string[];
}

function parseCSV(text: string): { headers: string[]; rows: string[][] } {
  const lines = text.split('\n').filter((l) => l.trim());
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
  const rows = lines.slice(1).map((line) => line.split(',').map((c) => c.trim()));
  return { headers, rows };
}

function validateCSV(headers: string[], rows: string[][]): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const entries: BindingEntry[] = [];

  // Check required columns
  const missingCols = REQUIRED_COLUMNS.filter((c) => !headers.includes(c));
  if (missingCols.length > 0) {
    return { valid: false, entries: [], warnings: [], errors: [`Missing required columns: ${missingCols.join(', ')}`] };
  }

  if (rows.length === 0) {
    return { valid: false, entries: [], warnings: [], errors: ['CSV has no data rows'] };
  }

  if (rows.length > MAX_BATCH_SIZE) {
    errors.push(`Too many rows (${rows.length}). Maximum is ${MAX_BATCH_SIZE} per batch.`);
    return { valid: false, entries: [], warnings, errors };
  }

  const unknownCols = headers.filter((h) => !REQUIRED_COLUMNS.includes(h) && !OPTIONAL_COLUMNS.includes(h));
  if (unknownCols.length > 0) {
    warnings.push(`Unknown columns will be ignored: ${unknownCols.join(', ')}`);
  }

  const colIdx = Object.fromEntries(headers.map((h, i) => [h, i]));

  // Track duplicates and conflicts
  const vectorIdSeen = new Set<string>();
  const duplicateVectorIds: string[] = [];
  const resourceGroups = new Map<string, BindingEntry[]>();

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const vectorId = row[colIdx.vector_id] ?? '';
    const extId = row[colIdx.external_resource_id] ?? '';

    if (!vectorId || !extId) {
      errors.push(`Row ${i + 2}: missing vector_id or external_resource_id`);
      continue;
    }

    if (vectorIdSeen.has(vectorId)) {
      duplicateVectorIds.push(vectorId);
    }
    vectorIdSeen.add(vectorId);

    const entry: BindingEntry = { vector_id: vectorId, external_resource_id: extId };
    if (colIdx.classification !== undefined && row[colIdx.classification]) {
      entry.classification = row[colIdx.classification];
    }
    if (colIdx.sensitivity !== undefined && row[colIdx.sensitivity]) {
      entry.sensitivity = row[colIdx.sensitivity];
    }
    if (colIdx.domain !== undefined && row[colIdx.domain]) {
      entry.domain = row[colIdx.domain];
    }
    if (colIdx.labels !== undefined && row[colIdx.labels]) {
      entry.labels = row[colIdx.labels].split(';').map((l) => l.trim()).filter(Boolean);
    }

    entries.push(entry);

    if (!resourceGroups.has(extId)) resourceGroups.set(extId, []);
    resourceGroups.get(extId)!.push(entry);
  }

  if (duplicateVectorIds.length > 0) {
    warnings.push(`${duplicateVectorIds.length} duplicate vector_id(s) detected`);
  }

  // Check for metadata conflicts within groups
  for (const [extId, group] of resourceGroups) {
    for (const field of ['classification', 'sensitivity', 'domain'] as const) {
      const values = new Set(group.map((e) => e[field]).filter(Boolean));
      if (values.size > 1) {
        warnings.push(`Conflicting ${field} for "${extId}" — server will reject this group`);
      }
    }
  }

  return { valid: errors.length === 0, entries, warnings, errors };
}

export function BindingDialog({ open, onOpenChange, connectorId, connectorName }: BindingDialogProps) {
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [previewRows, setPreviewRows] = useState<string[][]>([]);
  const [previewHeaders, setPreviewHeaders] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [result, setResult] = useState<BindResult | null>(null);
  const bindMutation = useBindMetadata();

  const reset = useCallback(() => {
    setValidation(null);
    setPreviewRows([]);
    setPreviewHeaders([]);
    setUploading(false);
    setProgress({ current: 0, total: 0 });
    setResult(null);
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setResult(null);

    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const { headers, rows } = parseCSV(text);
      setPreviewHeaders(headers);
      setPreviewRows(rows.slice(0, 10));
      setValidation(validateCSV(headers, rows));
    };
    reader.readAsText(f);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!validation?.valid || validation.entries.length === 0) return;

    setUploading(true);
    const entries = validation.entries;
    const totalBatches = Math.ceil(entries.length / MAX_BATCH_SIZE);
    setProgress({ current: 0, total: totalBatches });

    let aggregated: BindResult = {
      created_resources: 0,
      updated_resources: 0,
      created_chunks: 0,
      rebound_chunks: 0,
      errors: [],
      coverage_after: null,
    };

    for (let i = 0; i < totalBatches; i++) {
      const batch = entries.slice(i * MAX_BATCH_SIZE, (i + 1) * MAX_BATCH_SIZE);
      try {
        const batchResult = await bindMutation.mutateAsync({ id: connectorId, bindings: batch });
        aggregated = {
          created_resources: aggregated.created_resources + batchResult.created_resources,
          updated_resources: aggregated.updated_resources + batchResult.updated_resources,
          created_chunks: aggregated.created_chunks + batchResult.created_chunks,
          rebound_chunks: aggregated.rebound_chunks + batchResult.rebound_chunks,
          errors: [...aggregated.errors, ...batchResult.errors],
          coverage_after: batchResult.coverage_after,
        };
      } catch {
        aggregated.errors.push({ external_resource_id: 'batch_error', reason: `Batch ${i + 1} failed` });
      }
      setProgress({ current: i + 1, total: totalBatches });
    }

    setResult(aggregated);
    setUploading(false);
  }, [validation, connectorId, bindMutation]);

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) reset(); onOpenChange(o); }}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Bind Metadata — {connectorName}</DialogTitle>
          <DialogDescription>
            Map existing vectors to governed resources via CSV upload.
          </DialogDescription>
        </DialogHeader>

        {result ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-emerald-600">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-semibold">Binding Complete</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">Resources Created</p>
                <p className="font-bold text-lg">{result.created_resources}</p>
              </div>
              <div className="rounded bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">Resources Updated</p>
                <p className="font-bold text-lg">{result.updated_resources}</p>
              </div>
              <div className="rounded bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">Chunks Created</p>
                <p className="font-bold text-lg">{result.created_chunks}</p>
              </div>
              <div className="rounded bg-muted/50 p-3">
                <p className="text-muted-foreground text-xs">Chunks Rebound</p>
                <p className="font-bold text-lg">{result.rebound_chunks}</p>
              </div>
            </div>
            {result.coverage_after != null && (
              <p className="text-sm">Coverage now: ~{result.coverage_after}%</p>
            )}
            {result.errors.length > 0 && (
              <div className="space-y-1">
                <p className="text-sm font-medium text-red-600">{result.errors.length} error(s):</p>
                <div className="max-h-32 overflow-y-auto text-xs space-y-0.5">
                  {result.errors.map((err, i) => (
                    <p key={i} className="text-red-600">
                      {err.external_resource_id}: {err.reason}
                    </p>
                  ))}
                </div>
              </div>
            )}
            <DialogFooter>
              <Button onClick={() => { reset(); onOpenChange(false); }}>Done</Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">CSV File</label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Required: vector_id, external_resource_id. Optional: classification, sensitivity, domain, labels (semicolon-separated).
              </p>
            </div>

            {validation && (
              <div className="space-y-3">
                {validation.errors.length > 0 && (
                  <div className="rounded bg-red-50 dark:bg-red-900/10 p-3 text-sm text-red-600 space-y-1">
                    {validation.errors.map((e, i) => (
                      <p key={i} className="flex items-start gap-1">
                        <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />{e}
                      </p>
                    ))}
                  </div>
                )}
                {validation.warnings.length > 0 && (
                  <div className="rounded bg-amber-50 dark:bg-amber-900/10 p-3 text-sm text-amber-700 dark:text-amber-400 space-y-1">
                    {validation.warnings.map((w, i) => (
                      <p key={i} className="flex items-start gap-1">
                        <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />{w}
                      </p>
                    ))}
                  </div>
                )}
                {validation.valid && (
                  <p className="text-sm text-emerald-600 flex items-center gap-1">
                    <CheckCircle2 className="h-4 w-4" />
                    {validation.entries.length} entries ready to upload
                  </p>
                )}
              </div>
            )}

            {previewRows.length > 0 && (
              <div className="overflow-x-auto rounded border">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      {previewHeaders.map((h) => (
                        <th key={h} className="px-2 py-1 text-left font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row, i) => (
                      <tr key={i} className="border-b last:border-0">
                        {row.map((cell, j) => (
                          <td key={j} className="px-2 py-1 truncate max-w-[150px]">{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {validation && validation.entries.length > 10 && (
                  <p className="text-xs text-muted-foreground px-2 py-1">
                    Showing first 10 of {validation.entries.length} rows
                  </p>
                )}
              </div>
            )}

            {uploading && (
              <div className="space-y-2">
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Processing batch {progress.current} of {progress.total}...
                </p>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
              <Button
                onClick={handleUpload}
                disabled={!validation?.valid || uploading}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
