/**
 * Shared types used across multiple API domains.
 */

/** Pagination metadata returned by list endpoints. */
export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}
