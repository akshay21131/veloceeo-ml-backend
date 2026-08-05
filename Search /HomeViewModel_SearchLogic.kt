// Added to HomeViewModel.kt

var searchProducts = mutableStateListOf<Product>()
    private set
var searchStores = mutableStateListOf<StoreDetails>()
    private set

var isSearching by mutableStateOf(false)
    private set
var searchQuery by mutableStateOf("")
    private set

private var searchJob: Job? = null

fun onSearchQueryChanged(query: String) {
    searchQuery = query
    searchJob?.cancel()

    if (query.isBlank()) {
        isSearching = false
        searchProducts.clear()
        searchStores.clear()
        return
    }

    searchJob = viewModelScope.launch {
        delay(300)
        isSearching = true
        try {
            val response = dataManagerSearch.searchProductsAndStores(query)
            searchProducts.clear()
            searchProducts.addAll(response.products)
            searchStores.clear()
            searchStores.addAll(response.stores)
        } catch (_: Exception) {
            // Ignore error
        } finally {
            isSearching = false
        }
    }
}
