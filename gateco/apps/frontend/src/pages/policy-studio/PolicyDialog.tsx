import * as React from 'react';
import { Plus, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCreatePolicy, useUpdatePolicy } from '@/hooks/usePolicies';
import type { Policy, PolicyType, PolicyEffect, PolicyCondition, PolicyRule } from '@/types/policy';

const POLICY_TYPES: { value: PolicyType; label: string }[] = [
  { value: 'rbac', label: 'RBAC (Role-Based)' },
  { value: 'abac', label: 'ABAC (Attribute-Based)' },
  { value: 'rebac', label: 'ReBAC (Relationship-Based)' },
];

const OPERATORS: { value: PolicyCondition['operator']; label: string }[] = [
  { value: 'eq', label: 'equals' },
  { value: 'neq', label: 'not equals' },
  { value: 'in', label: 'in' },
  { value: 'not_in', label: 'not in' },
  { value: 'contains', label: 'contains' },
  { value: 'gte', label: '>=' },
  { value: 'lte', label: '<=' },
];

interface PolicyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  initialData?: Policy;
}

function emptyCondition(): PolicyCondition {
  return { field: '', operator: 'eq', value: '' };
}

function emptyRule(): PolicyRule {
  return {
    id: `rule_${Date.now()}`,
    description: '',
    effect: 'allow',
    conditions: [emptyCondition()],
    priority: 1,
  };
}

export function PolicyDialog({ open, onOpenChange, mode, initialData }: PolicyDialogProps) {
  const createMutation = useCreatePolicy();
  const updateMutation = useUpdatePolicy();
  const isPending = createMutation.isPending || updateMutation.isPending;

  const [name, setName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [type, setType] = React.useState<PolicyType>('rbac');
  const [effect, setEffect] = React.useState<PolicyEffect>('allow');
  const [rules, setRules] = React.useState<PolicyRule[]>([emptyRule()]);
  const [resourceSelectors, setResourceSelectors] = React.useState('');
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (open) {
      if (mode === 'edit' && initialData) {
        setName(initialData.name);
        setDescription(initialData.description);
        setType(initialData.type);
        setEffect(initialData.effect);
        setRules(initialData.rules.length > 0 ? initialData.rules : [emptyRule()]);
        setResourceSelectors(initialData.resource_selectors.join(', '));
      } else {
        setName('');
        setDescription('');
        setType('rbac');
        setEffect('allow');
        setRules([emptyRule()]);
        setResourceSelectors('');
      }
      setError('');
    }
  }, [open, mode, initialData]);

  function updateRule(index: number, updates: Partial<PolicyRule>) {
    setRules((prev) => prev.map((r, i) => (i === index ? { ...r, ...updates } : r)));
  }

  function updateCondition(ruleIndex: number, condIndex: number, updates: Partial<PolicyCondition>) {
    setRules((prev) =>
      prev.map((r, ri) =>
        ri === ruleIndex
          ? { ...r, conditions: r.conditions.map((c, ci) => (ci === condIndex ? { ...c, ...updates } : c)) }
          : r
      )
    );
  }

  function addCondition(ruleIndex: number) {
    setRules((prev) =>
      prev.map((r, i) => (i === ruleIndex ? { ...r, conditions: [...r.conditions, emptyCondition()] } : r))
    );
  }

  function removeCondition(ruleIndex: number, condIndex: number) {
    setRules((prev) =>
      prev.map((r, i) =>
        i === ruleIndex ? { ...r, conditions: r.conditions.filter((_, ci) => ci !== condIndex) } : r
      )
    );
  }

  function addRule() {
    setRules((prev) => [...prev, { ...emptyRule(), id: `rule_${Date.now()}`, priority: prev.length + 1 }]);
  }

  function removeRule(index: number) {
    setRules((prev) => prev.filter((_, i) => i !== index));
  }

  function validate(): string | null {
    if (!name.trim()) return 'Policy name is required';
    if (!description.trim()) return 'Description is required';
    if (rules.length === 0) return 'At least one rule is required';
    for (let i = 0; i < rules.length; i++) {
      const rule = rules[i];
      if (!rule.description.trim()) return `Rule ${i + 1}: description is required`;
      if (rule.conditions.length === 0) return `Rule ${i + 1}: at least one condition is required`;
      for (let j = 0; j < rule.conditions.length; j++) {
        const cond = rule.conditions[j];
        if (!cond.field.trim()) return `Rule ${i + 1}, Condition ${j + 1}: field is required`;
        if (cond.value === '' || (Array.isArray(cond.value) && cond.value.length === 0)) {
          return `Rule ${i + 1}, Condition ${j + 1}: value is required`;
        }
      }
    }
    return null;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const err = validate();
    if (err) {
      setError(err);
      return;
    }
    setError('');

    const selectors = resourceSelectors
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    const processedRules = rules.map((r) => ({
      ...r,
      conditions: r.conditions.map((c) => ({
        ...c,
        value: (c.operator === 'in' || c.operator === 'not_in') && typeof c.value === 'string'
          ? c.value.split(',').map((v) => v.trim())
          : c.value,
      })),
    }));

    const payload = {
      name: name.trim(),
      description: description.trim(),
      type,
      effect,
      rules: processedRules,
      resource_selectors: selectors,
    };

    if (mode === 'edit' && initialData) {
      updateMutation.mutate(
        { id: initialData.id, data: payload },
        {
          onSuccess: () => onOpenChange(false),
          onError: (err) => setError(err instanceof Error ? err.message : 'Failed to update policy'),
        }
      );
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => onOpenChange(false),
        onError: (err) => setError(err instanceof Error ? err.message : 'Failed to create policy'),
      });
    }
  }

  const selectClass = 'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{mode === 'create' ? 'Create Policy' : 'Edit Policy'}</DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Define a new access control policy with rules and conditions.'
              : 'Update policy configuration and rules.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My Policy" required />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Type</label>
              <select value={type} onChange={(e) => setType(e.target.value as PolicyType)} disabled={mode === 'edit'} className={selectClass}>
                {POLICY_TYPES.map((pt) => (
                  <option key={pt.value} value={pt.value}>{pt.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What does this policy do?" required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Default Effect</label>
              <select value={effect} onChange={(e) => setEffect(e.target.value as PolicyEffect)} className={selectClass}>
                <option value="allow">Allow</option>
                <option value="deny">Deny</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Resource Selectors</label>
              <Input
                value={resourceSelectors}
                onChange={(e) => setResourceSelectors(e.target.value)}
                placeholder="domain:engineering, label:pii"
              />
              <p className="text-xs text-muted-foreground">Comma-separated selectors</p>
            </div>
          </div>

          <div className="space-y-3 border-t pt-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Rules</h4>
              <Button type="button" variant="outline" size="sm" onClick={addRule}>
                <Plus className="h-3 w-3 mr-1" />Add Rule
              </Button>
            </div>

            {rules.map((rule, ri) => (
              <div key={rule.id} className="rounded-md border p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 space-y-2">
                    <Input
                      value={rule.description}
                      onChange={(e) => updateRule(ri, { description: e.target.value })}
                      placeholder="Rule description"
                      className="text-sm"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={rule.effect}
                      onChange={(e) => updateRule(ri, { effect: e.target.value as PolicyEffect })}
                      className="h-9 rounded-md border border-input bg-background px-2 text-sm"
                    >
                      <option value="allow">Allow</option>
                      <option value="deny">Deny</option>
                    </select>
                    {rules.length > 1 && (
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeRule(ri)}>
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground font-medium">Conditions</p>
                  {rule.conditions.map((cond, ci) => (
                    <div key={ci} className="flex items-center gap-2">
                      <Input
                        value={cond.field}
                        onChange={(e) => updateCondition(ri, ci, { field: e.target.value })}
                        placeholder="principal.group"
                        className="text-sm flex-1"
                      />
                      <select
                        value={cond.operator}
                        onChange={(e) => updateCondition(ri, ci, { operator: e.target.value as PolicyCondition['operator'] })}
                        className="h-9 rounded-md border border-input bg-background px-2 text-xs shrink-0"
                      >
                        {OPERATORS.map((op) => (
                          <option key={op.value} value={op.value}>{op.label}</option>
                        ))}
                      </select>
                      <Input
                        value={Array.isArray(cond.value) ? cond.value.join(', ') : String(cond.value)}
                        onChange={(e) => updateCondition(ri, ci, { value: e.target.value })}
                        placeholder="value or val1, val2"
                        className="text-sm flex-1"
                      />
                      {rule.conditions.length > 1 && (
                        <Button type="button" variant="ghost" size="sm" onClick={() => removeCondition(ri, ci)} className="shrink-0">
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button type="button" variant="ghost" size="sm" onClick={() => addCondition(ri)} className="text-xs">
                    <Plus className="h-3 w-3 mr-1" />Add Condition
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {error && (
            <p className="text-sm text-destructive bg-destructive/10 rounded-md p-2">{error}</p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Saving...' : mode === 'create' ? 'Create Policy' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
