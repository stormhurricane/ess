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
