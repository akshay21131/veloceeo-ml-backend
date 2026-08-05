package com.veloceeo.core.model.search

import com.veloceeo.core.model.product.Product
import com.veloceeo.core.model.store.StoreDetails
import kotlinx.serialization.Serializable

@Serializable
data class SearchRequest(
    val query: String,
)

@Serializable
data class SearchResponse(
    val products: List<Product> = emptyList(),
    val stores: List<StoreDetails> = emptyList(),
)
