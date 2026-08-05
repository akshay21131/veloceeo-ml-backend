package com.veloceeo.core.network.dataManager

import com.veloceeo.core.model.search.SearchResponse
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.functions.functions
import io.ktor.client.call.body
import io.ktor.client.request.forms.formData
import io.ktor.http.Headers
import io.ktor.http.HttpHeaders

class DataManagerImageSearch(
    private val supabaseClient: SupabaseClient,
) {
    suspend fun searchProductsByImage(imageBytes: ByteArray): SearchResponse {
        if (imageBytes.isEmpty()) return SearchResponse()

        return try {
            val response =
                supabaseClient.functions.invoke(
                    function = "search-by-image",
                    body =
                        formData {
                            append(
                                key = "file",
                                value = imageBytes,
                                headers =
                                    Headers.build {
                                        append(HttpHeaders.ContentType, "image/jpeg")
                                        append(HttpHeaders.ContentDisposition, "filename=\"search_query.jpg\"")
                                    },
                            )
                        },
                )
            response.body<SearchResponse>()
        } catch (_: Exception) {
            SearchResponse()
        }
    }
}
