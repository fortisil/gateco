import { useState } from 'react';
import { useAdminApi } from './useAdminApi';

interface ConnectionFormProps {
  onTestSuccess: (url: string) => void;
  onBack: () => void;
}

/**
 * Form to enter a DATABASE_URL and test the connection.
 * Calls POST /api/admin/db/test and reports success/failure.
 */
export function ConnectionForm({ onTestSuccess, onBack }: ConnectionFormProps) {
  const { callApi } = useAdminApi();
  const [url, setUrl] = useState('');
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  async function handleTest() {
    if (!url.trim()) return;
    setTesting(true);
    setResult(null);

    const res = await callApi<{ success: boolean; message: string }>(
      '/api/admin/db/test',
      { method: 'POST', body: { database_url: url } }
    );

    setTesting(false);

    if (res.data) {
      setResult(res.data);
      if (res.data.success) {
        onTestSuccess(url);
      }
    } else {
      setResult({ success: false, message: res.error || 'Connection failed' });
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="db-url" className="block text-sm font-medium text-gray-700 mb-1">
          DATABASE_URL
        </label>
        <input
          id="db-url"
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="postgresql://user:pass@host:5432/dbname"
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
        />
      </div>

      {result && (
        <div className={`text-sm p-3 rounded ${result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {result.message}
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleTest}
          disabled={testing || !url.trim()}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {testing ? 'Testing...' : 'Test Connection'}
        </button>
      </div>
    </div>
  );
}
