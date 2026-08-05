import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ⚠️ Ensure IMAGE_ML_SERVICE_URL matches your live Render service URL
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
    const contentType = req.headers.get("content-type") || "";
    let bodyData: any;
    let fetchHeaders: Record<string, string> = {};

    if (contentType.includes("multipart/form-data")) {
      bodyData = await req.formData();
    } else {
      const rawJson = await req.json();
      bodyData = JSON.stringify(rawJson);
      fetchHeaders["Content-Type"] = "application/json";
    }

    // 1. Forward image payload to Render CLIP Image ML Microservice
    const mlResponse = await fetch(IMAGE_ML_SERVICE_URL, {
      method: "POST",
      headers: fetchHeaders,
      body: bodyData,
    });

    const { product_ids } = await mlResponse.json();

    // 2. Fetch full product objects from Supabase DB using candidate product IDs
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "";
    const supabase = createClient(supabaseUrl, supabaseKey);

    const productsRes = await supabase
      .from("product")
      .select("*")
      .in("prod_id", product_ids || []);

    return new Response(
      JSON.stringify({
        products: productsRes.data ?? [],
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
