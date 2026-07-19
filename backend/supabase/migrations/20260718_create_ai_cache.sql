CREATE TABLE public.ai_cache (
    url_hash text PRIMARY KEY,
    url text NOT NULL,
    brain_data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for fast lookup by url_hash
CREATE INDEX IF NOT EXISTS idx_ai_cache_url_hash ON public.ai_cache (url_hash);
