/**
 * api.js
 * Centralized API & WebSocket URL resolution for OpenLore Studio.
 * Handles automatic protocol and host translation between browser mode and Electron desktop mode (file://).
 */

export function getApiBaseUrl() {
  if (typeof window !== 'undefined') {
    // In Electron standalone mode (loading via file:// protocol or without host)
    if (window.location.protocol === 'file:' || !window.location.host) {
      return 'http://127.0.0.1:8000';
    }
  }
  return '';
}

export function apiUrl(endpoint) {
  const base = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${base}${cleanEndpoint}`;
}

export function getWsUrl(endpoint = '/ws/live') {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  if (typeof window !== 'undefined') {
    if (window.location.protocol === 'file:' || !window.location.host) {
      return `ws://127.0.0.1:8000${cleanEndpoint}`;
    }
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProto}//${window.location.host}${cleanEndpoint}`;
  }
  return `ws://127.0.0.1:8000${cleanEndpoint}`;
}
