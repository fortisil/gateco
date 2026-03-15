'use client';

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center">
      <div className="text-center">
        <p className="text-7xl font-bold text-red-600">500</p>
        <h1 className="mt-4 text-3xl font-bold text-gray-900">Something went wrong</h1>
        <p className="mt-4 text-lg text-gray-600">
          An unexpected error occurred. Please try again.
        </p>
        <div className="mt-8">
          <button
            onClick={() => reset()}
            className="rounded-md bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-primary-500"
          >
            Try again
          </button>
        </div>
      </div>
    </main>
  );
}
