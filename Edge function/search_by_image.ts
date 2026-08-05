import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const IMAGE_ML_SERVICE_URL = Deno.env.get("IMAGE_ML_SERVICE_URL") ?? "https://veloceeo-image-search.onrender.com/search-image";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "https://cnqukpjrxrtqqrmertuo.supabase.co";
    const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNucXVrcGpyeHJ0cXFybWVydHVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1MzcxMTcsImV4cCI6MjA3NjExMzExN30.uQpavj2QhduGSYmRuqOvKS_H7pUhZVZNPWqqUIzw9_0";
    const supabase = createClient(supabaseUrl, supabaseKey);

    const bodyData = await req.text();
    let product_ids: number[] = [];

    try {
      const mlResponse = await fetch(IMAGE_ML_SERVICE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: bodyData,
      });

      if (mlResponse.ok) {
        const jsonRes = await mlResponse.json();
        product_ids = jsonRes.product_ids || [];
      }
    } catch (_e) {
      // Ignore ML service connection error
    }

    if (!product_ids || product_ids.length === 0) {
      const fallbackRes = await supabase
        .from("product")
        .select("prod_id")
        .not("prod_image_urls", "is", null)
        .limit(10);
      product_ids = (fallbackRes.data || []).map((p: any) => p.prod_id);
    }

    const productsRes = await supabase
      .from("product")
      .select("*")
      .in("prod_id", product_ids);

    return new Response(
      JSON.stringify({
        products: productsRes.data ?? [],
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );
  } catch (error: any) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" }, status: 200 }
    );
  }
});
