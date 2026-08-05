import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Replace with your deployed Python ML service URL (e.g. Railway, Render, Cloud Run)
const ML_SERVICE_URL = Deno.env.get("ML_SERVICE_URL") ?? "https://your-ml-api-service.com/predict";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { query } = await req.json();

    if (!query || typeof query !== "string" || query.trim() === "") {
      return new Response(
        JSON.stringify({ products: [], stores: [] }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
      );
    }

    // 1. Send query to ML Service to get vector matched IDs
    const mlResponse = await fetch(ML_SERVICE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query.trim() }),
    });

    const { product_ids, store_ids } = await mlResponse.json();

    // 2. Fetch full product & store records from Supabase DB
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "";
    const supabase = createClient(supabaseUrl, supabaseKey);

    const [productsRes, storesRes] = await Promise.all([
      supabase.from("product").select("*").in("prod_id", product_ids || []),
      supabase.from("store_details").select("*").in("store_id", store_ids || []),
    ]);

    return new Response(
      JSON.stringify({
        products: productsRes.data ?? [],
        stores: storesRes.data ?? [],
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 400 }
    );
  }
});
