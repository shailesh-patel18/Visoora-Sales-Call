export const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Generates the correct WebSocket URL for a given path based on the backend API URL.
 */
export const getWsUrl = (path: string): string => {
  const isSecure = BACKEND_URL.startsWith("https");
  const wsProtocol = isSecure ? "wss" : "ws";
  
  // Strip protocol prefix (http:// or https://)
  const base = BACKEND_URL.replace(/^https?:\/\//, "");
  
  // Normalize leading slash on path
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  
  return `${wsProtocol}://${base}${normalizedPath}`;
};
