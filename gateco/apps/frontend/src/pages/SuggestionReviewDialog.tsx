import { useState } from 'react';
import { Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { suggestClassifications, applySuggestions } from '@/api/connectors';
import type { ClassificationSuggestion, SuggestClassificationsResponse, ApplySuggestionsResponse } from '@/types/connector';

interface SuggestionReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  connectorId: string;
  connectorName: string;
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  if (confidence >= 0.8) {
    return <span className="text-xs font-medium text-emerald-700 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-900/20 rounded px-1.5 py-0.5">{(confidence * 100).toFixed(0)}%</span>;
  }
  if (confidence >= 0.5) {
    return <span className="text-xs font-medium text-yellow-700 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20 rounded px-1.5 py-0.5">{(confidence * 100).toFixed(0)}%</span>;
  }
  return <span className="text-xs font-medium text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-900/20 rounded px-1.5 py-0.5">{(confidence * 100).toFixed(0)}%</span>;
}

export function SuggestionReviewDialog({ open, onOpenChange, connectorId, connectorName }: SuggestionReviewDialogProps) {
  const [step, setStep] = useState<'idle' | 'analyzing' | 'review' | 'applying' | 'done'>('idle');
  const [suggestions, setSuggestions] = useState<ClassificationSuggestion[]>([]);
  const [scannedVectors, setScannedVectors] = useState(0);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [applyResult, setApplyResult] = useState<ApplySuggestionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    setStep('analyzing');
    setError(null);
    try {
      const result = await suggestClassifications(connectorId, { scan_limit: 1000 });
      setSuggestions(result.suggestions);
      setScannedVectors(result.scanned_vectors);
      setSelected(new Set(result.suggestions.map((_, i) => i)));
      setStep('review');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed');
      setStep('idle');
    }
  }

  async function handleApply() {
    setStep('applying');
    setError(null);
    const toApply = suggestions.filter((_, i) => selected.has(i));
    try {
      const result = await applySuggestions(connectorId, toApply);
      setApplyResult(result);
      setStep('done');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Apply failed');
      setStep('review');
    }
  }

  function toggleSelection(index: number) {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }

  function selectAll() {
    setSelected(new Set(suggestions.map((_, i) => i)));
  }

  function selectNone() {
    setSelected(new Set());
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card rounded-lg shadow-xl border max-w-4xl w-full mx-4 max-h-[80vh] flex flex-col">
        <div className="p-6 border-b flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Suggest Classifications</h2>
            <p className="text-sm text-muted-foreground">{connectorName}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>Close</Button>
        </div>

        <div className="p-6 overflow-auto flex-1">
          {error && (
            <div className="mb-4 rounded bg-red-50 dark:bg-red-900/10 p-3 text-sm text-red-700 dark:text-red-400 flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}

          {step === 'idle' && (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">
                Analyze vectors in this connector to suggest classifications based on naming patterns.
              </p>
              <Button onClick={handleAnalyze}>Analyze Vectors</Button>
            </div>
          )}

          {step === 'analyzing' && (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">Scanning vectors and generating suggestions...</p>
            </div>
          )}

          {step === 'review' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {scannedVectors} vectors scanned, {suggestions.length} suggestions generated
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={selectAll}>Select All</Button>
                  <Button variant="outline" size="sm" onClick={selectNone}>Select None</Button>
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="p-2 text-left w-8"></th>
                      <th className="p-2 text-left">Resource Key</th>
                      <th className="p-2 text-left">Vectors</th>
                      <th className="p-2 text-left">Classification</th>
                      <th className="p-2 text-left">Sensitivity</th>
                      <th className="p-2 text-left">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {suggestions.map((s, i) => (
                      <tr
                        key={s.resource_key}
                        className={`border-t hover:bg-muted/30 cursor-pointer ${selected.has(i) ? 'bg-primary/5' : ''}`}
                        onClick={() => toggleSelection(i)}
                      >
                        <td className="p-2">
                          <input
                            type="checkbox"
                            checked={selected.has(i)}
                            onChange={() => toggleSelection(i)}
                            className="rounded"
                          />
                        </td>
                        <td className="p-2 font-mono text-xs truncate max-w-[200px]" title={s.resource_key}>
                          {s.resource_key}
                        </td>
                        <td className="p-2">{s.vector_ids.length}</td>
                        <td className="p-2">{s.suggested_classification ?? '—'}</td>
                        <td className="p-2">{s.suggested_sensitivity ?? '—'}</td>
                        <td className="p-2">
                          <div className="flex items-center gap-2">
                            <ConfidenceBadge confidence={s.confidence} />
                            {s.reasoning && (
                              <span className="text-xs text-muted-foreground truncate max-w-[150px]" title={s.reasoning}>
                                {s.reasoning}
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {step === 'applying' && (
            <div className="text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">Applying selected suggestions...</p>
            </div>
          )}

          {step === 'done' && applyResult && (
            <div className="text-center py-8 space-y-3">
              <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto" />
              <p className="font-medium">Suggestions Applied</p>
              <div className="text-sm text-muted-foreground space-y-1">
                <p>{applyResult.applied} suggestions applied</p>
                <p>{applyResult.resources_created} resources created</p>
                {applyResult.errors.length > 0 && (
                  <p className="text-red-600">{applyResult.errors.length} errors</p>
                )}
              </div>
            </div>
          )}
        </div>

        {step === 'review' && (
          <div className="p-4 border-t flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button onClick={handleApply} disabled={selected.size === 0}>
              Apply {selected.size} Selected
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
