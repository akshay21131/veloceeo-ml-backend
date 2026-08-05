// Common Project Files Registration Snippets

// 1. Constants.kt (core/common/src/commonMain/kotlin/com/veloceeo/core/common/utils/Constants.kt)
const val SEARCH_PRODUCTS_STORES = "search-products-stores"

// 2. DataManagerModule.kt (core/network/src/commonMain/kotlin/com/veloceeo/core/network/di/DataManagerModule.kt)
val dataManagerModule = module {
    // ... existing data managers ...
    singleOf(::DataManagerSearch)
}

// 3. StoreDetails SerialName Mappings in Store.kt (core/model/src/commonMain/kotlin/com/veloceeo/core/model/store/Store.kt)
@Serializable
data class StoreDetails(
    @SerialName("store_id") val storeId: Int? = null,
    @SerialName("store_uuid") val storeUuid: String? = null,
    @SerialName("store_name") val storeName: String? = null,
    @SerialName("store_email") val storeEmail: String? = null,
    @SerialName("store_mobile_no") val storeMobileNo: String? = null,
    @SerialName("store_address") val storeAddress: String? = null,
    @SerialName("store_district") val storeDistrict: String? = null,
    @SerialName("store_state") val storeState: String? = null,
    @SerialName("is_active") val isActive: Boolean? = true,
)

// 4. core/ui/build.gradle.kts
kotlin {
    sourceSets {
        androidMain {
            dependencies {
                implementation(libs.androidx.activity.compose)
            }
        }
    }
}
