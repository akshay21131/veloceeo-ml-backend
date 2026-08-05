// Added to HomeViewModel.kt for Image Search

fun onImageSelected(imageBytes: ByteArray) {
    searchJob?.cancel()
    searchQuery = "Visual Image Search"
    isSearching = true

    viewModelScope.launch {
        try {
            val response = dataManagerImageSearch.searchProductsByImage(imageBytes)
            searchProducts.clear()
            searchProducts.addAll(response.products)
            searchStores.clear()
        } catch (_: Exception) {
            // Ignore error
        } finally {
            isSearching = false
        }
    }
}
