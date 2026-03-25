/**
 * Translates HTTP error codes into user-friendly messages.
 * Never exposes raw error details to users for security.
 */
export function translateApiError(status: number, detail?: string): string {
  switch (status) {
    case 504:
      return "This is taking longer than usual. Please try again.";
    case 503:
      return "Service temporarily busy. Please wait a moment and retry.";
    case 502:
      return "Could not parse this format. Please try a different file.";
    case 401:
      return "Session expired. Please refresh the page.";
    case 409:
      return detail ?? "This action conflicts with the current state.";
    case 422:
      return detail ?? "Invalid input. Please check your entries.";
    case 404:
      return "The requested resource was not found.";
    case 429:
      return "Too many requests. Please wait a moment and try again.";
    case 500:
      return "An internal error occurred. Please try again later.";
    default:
      return detail ?? `An error occurred (${status}). Please try again.`;
  }
}

/**
 * Extracts error message from API response.
 * Safely handles various response formats.
 */
export async function extractApiError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = body.detail;
    
    if (typeof detail === "string") {
      return detail;
    }
    
    if (Array.isArray(detail)) {
      return detail
        .map((e: { msg?: string }) => e.msg ?? JSON.stringify(e))
        .join("; ");
    }
    
    if (detail?.message) {
      return detail.message;
    }
    
    return res.statusText || `HTTP ${res.status}`;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

/**
 * Combines error extraction and translation.
 */
export async function getApiErrorMessage(res: Response): Promise<string> {
  const detail = await extractApiError(res);
  return translateApiError(res.status, detail);
}