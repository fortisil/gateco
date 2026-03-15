import { useMemo, useCallback, useRef } from 'react';

export function useFormDirty<T extends Record<string, unknown>>(
  initialValues: T,
  currentValues: T
) {
  const snapshotRef = useRef(initialValues);

  const isDirty = useMemo(() => {
    const snapshot = snapshotRef.current;
    return Object.keys(currentValues).some(
      (key) => currentValues[key] !== snapshot[key]
    );
  }, [currentValues]);

  const resetDirty = useCallback(() => {
    snapshotRef.current = { ...currentValues };
  }, [currentValues]);

  return { isDirty, resetDirty };
}
