/**
 * Map API / fetch errors to short German UI messages (J1).
 * Safe to call on already-friendly strings (returns them unchanged when unknown).
 */

/** Shared fetch options so browsers/CDNs do not return empty 304 bodies. */
export const API_FETCH_INIT: RequestInit = {
  cache: "no-store",
  // Needed so Basic Auth from the browser login prompt is sent on API calls.
  credentials: "same-origin",
  headers: {
    "Cache-Control": "no-cache",
    Pragma: "no-cache",
  },
};

export function friendlyApiError(
  raw: string | undefined,
  status?: number,
): string {
  const message = (raw ?? "").trim();

  if (status === 401) {
    return "Nicht angemeldet. Bitte unter /login anmelden.";
  }
  if (status === 304) {
    return "Veraltete Zwischenspeicherung — bitte Seite neu laden (Hard-Reload).";
  }
  if (status === 403) {
    return "Kein Zugriff — Rechte oder Zugangsdaten prüfen.";
  }
  if (status === 404) {
    if (/workflow/i.test(message)) {
      return "Scrape-Workflow nicht gefunden (Repo oder Dateiname prüfen).";
    }
    if (/File not found|config\.yaml|result\.json/i.test(message)) {
      return "Datei in ess-data nicht gefunden.";
    }
    return "Nicht gefunden.";
  }
  if (status === 409) {
    return "Konflikt: Die Config wurde parallel geändert. Bitte neu laden und erneut speichern.";
  }

  if (/Invalid credentials|Authentication required/i.test(message)) {
    return "Nicht angemeldet oder Zugangsdaten falsch.";
  }
  if (/Missing environment variable/i.test(message)) {
    return "Server-Konfiguration unvollständig (Umgebungsvariable fehlt).";
  }
  if (/must be in the form owner\/repo/i.test(message)) {
    return "Server-Konfiguration ungültig (Repo-Angabe).";
  }
  if (/GitHub authentication or permission failed/i.test(message)) {
    return "GitHub-Zugriff fehlgeschlagen — Token oder Rechte prüfen.";
  }
  if (/Conflict updating|SHA mismatch/i.test(message)) {
    return "Konflikt: Die Config wurde parallel geändert. Bitte neu laden und erneut speichern.";
  }
  if (/GitHub Contents API/i.test(message)) {
    return "GitHub konnte die Datei nicht lesen oder speichern. Später erneut versuchen.";
  }
  if (/GitHub workflow_dispatch/i.test(message)) {
    return "Scrape konnte bei GitHub nicht gestartet werden.";
  }
  if (/GitHub workflow runs/i.test(message)) {
    return "Scrape-Status konnte bei GitHub nicht geladen werden.";
  }
  if (/Unexpected GitHub/i.test(message)) {
    return "Unerwartete Antwort von GitHub.";
  }
  if (/Invalid YAML in config\.yaml/i.test(message)) {
    return "config.yaml in ess-data ist kein gültiges YAML.";
  }
  if (/config\.yaml must parse/i.test(message)) {
    return "config.yaml hat ein unerwartetes Format.";
  }
  if (/Invalid JSON in result\.json/i.test(message)) {
    return "result.json in ess-data ist kein gültiges JSON.";
  }
  if (/result\.json must parse/i.test(message)) {
    return "result.json hat ein unerwartetes Format.";
  }
  if (/Request body must be valid JSON/i.test(message)) {
    return "Ungültige Anfrage (JSON).";
  }
  if (/Request body must be a JSON object/i.test(message)) {
    return "Ungültige Anfrage (JSON-Objekt erwartet).";
  }
  if (/Unknown field:/i.test(message)) {
    return "Ungültige Config: unbekanntes Feld.";
  }
  if (/name must not be empty/i.test(message)) {
    return "Ein Name ist leer — bitte ausfüllen.";
  }
  if (/contains duplicate name:/i.test(message)) {
    const name = message.split(":").slice(1).join(":").trim();
    return name
      ? `Doppelter Name: „${name}“.`
      : "Doppelter Name in der Config.";
  }
  if (/nations\[.*\] must not be empty/i.test(message)) {
    return "Ein Nationen-Code ist leer.";
  }
  if (/nations contains duplicate:/i.test(message)) {
    const code = message.split(":").slice(1).join(":").trim();
    return code
      ? `Doppelte Nation: „${code}“.`
      : "Doppelte Nation in der Config.";
  }
  if (/must be an array|must be a string|must be a boolean|must be a string or object/i.test(message)) {
    return "Ungültige Config-Struktur.";
  }
  if (/File not found:/i.test(message)) {
    return "Datei in ess-data nicht gefunden.";
  }
  if (/Workflow .+ not found/i.test(message)) {
    return "Scrape-Workflow nicht gefunden (Repo oder Dateiname prüfen).";
  }
  if (/Antwort ist kein gültiges JSON/i.test(message)) {
    return "Server-Antwort ungültig.";
  }
  if (/^Fehler \d+$/.test(message)) {
    const code = Number(message.replace(/\D/g, "")) || status;
    return friendlyApiError(undefined, code);
  }

  if (status === 400) {
    return message || "Ungültige Eingabe.";
  }
  if (status === 500) {
    return message || "Interner Serverfehler.";
  }
  if (status === 502) {
    return message || "Externer Dienst (GitHub) nicht erreichbar oder fehlerhaft.";
  }
  if (status && status >= 400) {
    return message || `Anfrage fehlgeschlagen (Fehler ${status}).`;
  }

  return message || "Unbekannter Fehler.";
}

/** Format thrown errors from fetch/UI actions. */
export function friendlyCaughtError(
  error: unknown,
  fallback = "Unbekannter Fehler.",
): string {
  if (error instanceof TypeError) {
    return "Keine Verbindung zum Server.";
  }
  if (error instanceof Error && error.message) {
    return friendlyApiError(error.message);
  }
  return fallback;
}
