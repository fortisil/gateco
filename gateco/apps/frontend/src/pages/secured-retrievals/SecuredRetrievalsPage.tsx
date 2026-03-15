import { Shield } from 'lucide-react';

export function SecuredRetrievalsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Secured Retrievals</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Monitor all retrieval operations: timestamps, principals, queries, policy evaluations, and outcomes.
        </p>
      </div>

      <div className="rounded-lg border border-dashed p-12 text-center">
        <Shield className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold">Retrieval Timeline</h3>
        <p className="text-sm text-muted-foreground mt-1">
          The retrieval timeline with full policy traces and filtering is coming in the next release.
        </p>
      </div>
    </div>
  );
}
