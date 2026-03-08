export type AuthUser = {
  id: string;
  email: string;
  username: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: AuthUser;
};

export type LoginPayload = {
  identifier: string;
  password: string;
};

export type RegisterPayload = {
  email: string;
  username: string;
  password: string;
};

export type SummaryCategory = {
  category: string;
  amount: number;
};

export type SummaryResponse = {
  currency: string;
  total_spent: number;
  categories: SummaryCategory[];
};

export type ApiMessage = {
  message: string;
};

export type IngestionMode = "single_upload" | "inbox_sync" | "statement_import";

export type IngestionMessageInput = {
  message: string;
  source_message_id?: string | null;
  source_received_at?: string | null;
  user_note?: string | null;
  source?: string | null;
};

export type TransactionRecord = {
  id: number;
  amount: number;
  currency: string;
  category: string;
  direction: string;
  transaction_type?: string | null;
  recipient?: string | null;
  reference?: string | null;
  occurred_at?: string | null;
  date?: string | null;
  time?: string | null;
  user_note?: string | null;
  ingestion_mode: IngestionMode | string;
  ingestion_batch_id?: string | null;
  source_message_id?: string | null;
  source_received_at?: string | null;
  source: string;
};

export type IngestMessagesPayload = {
  mode: IngestionMode;
  batch_id?: string | null;
  user_note?: string | null;
  source?: string | null;
  messages: IngestionMessageInput[];
};

export type IngestionItemResult = {
  index: number;
  status: "stored" | "duplicate" | "failed";
  source_message_id?: string | null;
  error?: string | null;
  transaction?: TransactionRecord | null;
};

export type IngestMessagesResponse = {
  mode: IngestionMode;
  batch_id: string;
  total: number;
  stored: number;
  duplicates: number;
  failed: number;
  results: IngestionItemResult[];
};
