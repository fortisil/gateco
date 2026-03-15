export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
    request_id?: string;
  };
}

export class ApiRequestError extends Error {
  code: string;
  status: number;
  details?: Record<string, string[]>;
  requestId?: string;

  constructor(error: ApiError['error'], status: number) {
    super(error.message);
    this.name = 'ApiRequestError';
    this.code = error.code;
    this.status = status;
    this.details = error.details;
    this.requestId = error.request_id;
  }
}
