export interface ProductInput {
  sku: string;
  name: string;
  category: string;
  target_audience: string;
  technical_attributes: Record<string, string>;
  key_benefits: string[];
}
export interface Product extends ProductInput {
  id: string;
  created_at: string;
  updated_at: string;
}
export type Tone =
  "persuasivo" | "descontraído" | "institucional" | "promocional";
export interface Copy {
  id: string;
  product_id: string;
  input_hash: string;
  tone_of_voice: Tone;
  instagram_copy: {
    hook: string;
    caption: string;
    hashtags: string[];
    call_to_action: string;
  };
  whatsapp_copy: { message: string; call_to_action: string };
  seo_copy: {
    meta_title: string;
    meta_description: string;
    bullet_points: string[];
    long_description: string;
  };
  input_snapshot: { product: ProductInput };
  model_name: string;
  inference_time_ms: number;
  tokens_used: number;
  created_at: string;
}
export interface Generation {
  copy: Copy;
  cache_status: "HIT" | "MISS";
}
export interface Metric {
  id: string;
  request_id: string;
  path: string;
  method: string;
  latency_ms: number;
  cache_status: string;
  status_code: number;
  input_hash: string | null;
  model_name: string | null;
  tokens_used: number;
  tokens_saved: number;
  created_at: string;
}
export interface Summary {
  provider: string;
  model_name: string;
  generation_requests: number;
  successful_generations: number;
  errors: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_ratio: number | null;
  average_latency_ms: number | null;
  hit_latency_ms: number | null;
  miss_latency_ms: number | null;
  latency_savings_percent: number | null;
  tokens_used: number;
  estimated_tokens_saved: number;
  estimated_token_savings_percent: number | null;
}
export interface Page<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}
