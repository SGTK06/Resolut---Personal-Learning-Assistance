/**
 * API base URL for the local backend.
 * In dev, use empty string so Vite proxy forwards /api to the backend.
 * Override with VITE_API_BASE_URL (e.g. http://localhost:8000) if not using proxy.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
