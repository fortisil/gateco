/**
 * Pagination helpers for list endpoints.
 */

/** A single page of results from a paginated API endpoint. */
export interface Page<T> {
  /** The list of items on this page. */
  items: T[];
  /** Current page number (1-based). */
  page: number;
  /** Maximum items per page. */
  perPage: number;
  /** Total number of items across all pages. */
  total: number;
  /** Total number of pages. */
  totalPages: number;
}

/**
 * Extract pagination metadata from the raw API response envelope.
 *
 * The backend returns `{ data: [...], meta: { pagination: {...} } }`.
 */
export function parsePage<T>(
  raw: Record<string, unknown> | null,
  page: number,
  perPage: number,
  parseItem: (item: Record<string, unknown>) => T,
): Page<T> {
  const data = (raw && Array.isArray(raw["data"]) ? raw["data"] : []) as Record<string, unknown>[];
  const meta = (raw && typeof raw["meta"] === "object" && raw["meta"] !== null
    ? raw["meta"]
    : {}) as Record<string, unknown>;
  const pagination = (typeof meta["pagination"] === "object" && meta["pagination"] !== null
    ? meta["pagination"]
    : {}) as Record<string, unknown>;

  const items = data.map(parseItem);

  return {
    items,
    page: typeof pagination["page"] === "number" ? pagination["page"] : page,
    perPage: typeof pagination["per_page"] === "number" ? pagination["per_page"] : perPage,
    total: typeof pagination["total"] === "number" ? pagination["total"] : items.length,
    totalPages: typeof pagination["total_pages"] === "number" ? pagination["total_pages"] : 1,
  };
}

/** Type for the fetch callback used by `listAll`. */
export type FetchFn = (page: number, perPage: number) => Promise<Record<string, unknown> | null>;

/**
 * AsyncGenerator-based paginator that lazily yields all items across
 * every page of a paginated endpoint.
 *
 * @example
 * ```ts
 * for await (const connector of listAll(fetchFn, parseConnector)) {
 *   console.log(connector.name);
 * }
 * ```
 */
export async function* listAll<T>(
  fetch: FetchFn,
  parseItem: (item: Record<string, unknown>) => T,
  perPage = 100,
): AsyncGenerator<T, void, undefined> {
  let page = 1;
  while (true) {
    const raw = await fetch(page, perPage);

    const data = (raw && Array.isArray(raw["data"]) ? raw["data"] : []) as Record<
      string,
      unknown
    >[];
    for (const itemData of data) {
      yield parseItem(itemData);
    }

    // Determine if there are more pages.
    const meta = (raw && typeof raw["meta"] === "object" && raw["meta"] !== null
      ? raw["meta"]
      : {}) as Record<string, unknown>;
    const pagination = (typeof meta["pagination"] === "object" && meta["pagination"] !== null
      ? meta["pagination"]
      : {}) as Record<string, unknown>;
    const totalPages = typeof pagination["total_pages"] === "number" ? pagination["total_pages"] : 1;

    if (page >= totalPages || data.length === 0) {
      break;
    }
    page++;
  }
}

/**
 * Collect all items from an async generator into an array.
 */
export async function collectAll<T>(gen: AsyncGenerator<T, void, undefined>): Promise<T[]> {
  const results: T[] = [];
  for await (const item of gen) {
    results.push(item);
  }
  return results;
}
