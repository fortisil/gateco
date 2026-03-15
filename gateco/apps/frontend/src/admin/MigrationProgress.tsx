import { useState, useEffect, useRef } from 'react';
import { useAdminApi } from './useAdminApi';

interface StepResult {
  step: string;
  success: boolean;
  message: string;
}

interface MigrationProgressProps {
  databaseUrl: string;
  onComplete: () => void;
  onError: (msg: string) => void;
}

/**
 * Runs POST /api/admin/db/apply then polls GET /api/admin/db/status
 * every 2 seconds while in "applying" state.
 * Shows a step-by-step progress list.
 */
export function MigrationProgress({ databaseUrl, onComplete, onError }: MigrationProgressProps) {
  const { callApi } = useAdminApi();
  const [steps, setSteps] = useState<StepResult[]>([]);
  const [applying, setApplying] = useState(true);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    async function runApply() {
      const res = await callApi<{ steps: StepResult[]; status: string }>(
        '/api/admin/db/apply',
        { method: 'POST', body: { database_url: databaseUrl } }
      );

      if (res.data) {
        setSteps(res.data.steps);
        if (res.data.status === 'ready') {
          setApplying(false);
          onComplete();
        } else if (res.data.status === 'error') {
          setApplying(false);
          const failedStep = res.data.steps.find((s) => !s.success);
          onError(failedStep?.message || 'Setup failed');
        }
      } else {
        setApplying(false);
        onError(res.error || 'Failed to apply setup');
      }
    }

    runApply();
  }, [databaseUrl]);

  useEffect(() => {
    if (!applying) return;

    const interval = setInterval(async () => {
      const res = await callApi<{ status: string }>('/api/admin/db/status');
      if (res.data) {
        if (res.data.status === 'ready') {
          setApplying(false);
          onComplete();
        } else if (res.data.status === 'error') {
          setApplying(false);
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [applying]);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700">Applying Setup</h3>
      <ul className="space-y-2">
        {steps.map((step, i) => (
          <li key={i} className="flex items-center gap-2 text-sm">
            <span className={`inline-block w-4 h-4 rounded-full flex items-center justify-center text-xs ${
              step.success ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
            }`}>
              {step.success ? '\u2713' : '\u2717'}
            </span>
            <span className={step.success ? 'text-gray-700' : 'text-red-700'}>
              {step.message}
            </span>
          </li>
        ))}
        {applying && (
          <li className="flex items-center gap-2 text-sm text-gray-500">
            <span className="inline-block w-4 h-4 rounded-full bg-blue-100 animate-pulse" />
            Running...
          </li>
        )}
      </ul>
    </div>
  );
}
