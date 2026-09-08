export type Hit = {
  location?: string;
  date?: string;
  url?: string;
};

export type ResultsPayload = {
  gefundene_reiter?: Record<string, Hit[]>;
  gefundene_pferde?: Record<string, Hit[]>;
};

export type ApiErrorBody = {
  error?: string;
};
