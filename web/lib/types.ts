export type Hit = {
  location?: string;
  date?: string;
  url?: string;
};

export type ResultsPayload = {
  gefundene_reiter?: Record<string, Hit[]>;
  gefundene_pferde?: Record<string, Hit[]>;
};

export type ConfigEntry = string | { name?: string; title?: string; active?: boolean };

export type ConfigPayload = {
  riders?: ConfigEntry[];
  horses?: ConfigEntry[];
  nations?: string[];
};

export type ApiErrorBody = {
  error?: string;
};

export type ScrapeRun = {
  id: number;
  status: string;
  conclusion: string | null;
  event: string;
  created_at: string;
  updated_at: string;
  html_url: string;
};

export type ScrapeStatusPayload = {
  workflow: string;
  run: ScrapeRun | null;
};

export type ScrapeDispatchPayload = {
  ok?: boolean;
  workflow?: string;
  ref?: string;
};
