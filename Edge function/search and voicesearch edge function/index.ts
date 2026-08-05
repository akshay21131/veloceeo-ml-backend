import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

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

    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "";
    const supabase = createClient(supabaseUrl, supabaseKey);

    const searchTerm = `%${query.trim()}%`;

    const [productsRes, storesRes] = await Promise.all([
      supabase
        .from("product")
        .select("*")
        .or(`prod_name.ilike.${searchTerm},prod_description.ilike.${searchTerm},category.ilike.${searchTerm},brand.ilike.${searchTerm}`)
        .limit(25),
      
      supabase
        .from("store_details")
        .select("*")
        .or(`store_name.ilike.${searchTerm},store_address.ilike.${searchTerm},store_district.ilike.${searchTerm},store_state.ilike.${searchTerm}`)
        .limit(10)
    ]);

    return new Response(
      JSON.stringify({
        products: productsRes.data ?? [],
        stores: storesRes.data ?? []
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
