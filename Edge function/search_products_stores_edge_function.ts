import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const ML_SERVICE_URL = Deno.env.get("ML_SERVICE_URL") ?? "https://veloceeo-ml-search.onrender.com/predict";

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

    // 1. Send query to Render ML Microservice
    const mlResponse = await fetch(ML_SERVICE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query.trim() }),
    });

    const { product_ids, store_ids } = await mlResponse.json();

    // 2. Fetch full product & store objects from Supabase DB
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "";
    const supabase = createClient(supabaseUrl, supabaseKey);

    const [productsRes, storesRes] = await Promise.all([
      supabase.from("product").select("*").in("prod_id", product_ids || []),
      supabase.from("store_details").select("*").in("store_id", store_ids || []),
    ]);

    // 3. Preserve ML relevance ranking order
    const sortedProducts = (productsRes.data ?? []).sort((a, b) => {
      return (product_ids || []).indexOf(a.prod_id) - (product_ids || []).indexOf(b.prod_id);
    });

    const sortedStores = (storesRes.data ?? []).sort((a, b) => {
      return (store_ids || []).indexOf(a.store_id) - (store_ids || []).indexOf(b.store_id);
    });

    return new Response(
      JSON.stringify({
        products: sortedProducts,
        stores: sortedStores,
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
