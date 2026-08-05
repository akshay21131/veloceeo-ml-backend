package com.veloceeo.core.network.dataManager

import com.veloceeo.core.common.utils.Constants
import com.veloceeo.core.model.product.Product
import com.veloceeo.core.model.search.SearchRequest
import com.veloceeo.core.model.search.SearchResponse
import com.veloceeo.core.model.store.StoreDetails
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.functions.functions
import io.github.jan.supabase.postgrest.from
import io.ktor.client.call.body

class DataManagerSearch(
    private val supabaseClient: SupabaseClient,
) {
    suspend fun searchProductsAndStores(query: String): SearchResponse {
        if (query.isBlank()) return SearchResponse()

        return try {
            val response =
                supabaseClient.functions.invoke(
                    function = Constants.SEARCH_PRODUCTS_STORES,
                    body = SearchRequest(query = query),
                )
            response.body<SearchResponse>()
        } catch (_: Exception) {
            val products =
                try {
                    supabaseClient
                        .from(Constants.PRODUCT)
                        .select {
                            filter {
                                ilike("prod_name", "%$query%")
                            }
                        }.decodeList<Product>()
                } catch (_: Exception) {
                    emptyList()
                }

            val stores =
                try {
                    supabaseClient
                        .from(Constants.STORE_DETAILS)
                        .select {
                            filter {
                                ilike("store_name", "%$query%")
                            }
                        }.decodeList<StoreDetails>()
                } catch (_: Exception) {
                    emptyList()
                }

            SearchResponse(
                products = products,
                stores = stores,
            )
        }
    }
}
