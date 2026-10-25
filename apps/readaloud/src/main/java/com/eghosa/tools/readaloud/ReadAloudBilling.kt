package com.eghosa.tools.readaloud

import androidx.activity.ComponentActivity
import androidx.compose.runtime.mutableStateOf
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class PremiumOffer(val basePlanId: String, val label: String,
                        val displayPrice: String, val offerToken: String)

/**
 * Only a successful HTTPS response from the Google Play Developer API verifier
 * may activate Premium. A local purchase callback by itself is never sufficient.
 */
class ReadAloudBilling(
    private val activity: ComponentActivity,
    private val controller: PlaybackController
) : PurchasesUpdatedListener {
    val billingAvailable = mutableStateOf(false)
    val offers = mutableStateOf(emptyList<PremiumOffer>())
    val message = mutableStateOf("Premium checkout is not yet configured.")
    private val scope = CoroutineScope(Dispatchers.Main)
    private var details: ProductDetails? = null
    private val verifierReady = BuildConfig.BILLING_VERIFIER_URL.startsWith("https://") &&
        BuildConfig.BILLING_VERIFIER_URL.endsWith("/verify")
    private val client = BillingClient.newBuilder(activity.applicationContext)
        .setListener(this)
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
        .enableAutoServiceReconnection()
        .build()

    fun start() {
        if (!verifierReady) {
            message.value = "Checkout disabled until a secure Google Play verification endpoint is configured."
            return
        }
        client.startConnection(object : BillingClientStateListener {
            override fun onBillingServiceDisconnected() {
                billingAvailable.value = false
                message.value = "Google Play connection lost."
            }
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                    message.value = "Google Play Billing unavailable on this device."
                    return
                }
                refreshOffers()
                restorePurchases()
            }
        })
    }

    private fun refreshOffers() {
        if (!client.isReady) return
        val request = QueryProductDetailsParams.newBuilder().setProductList(
            listOf(QueryProductDetailsParams.Product.newBuilder()
                .setProductId("readaloud_premium")
                .setProductType(BillingClient.ProductType.SUBS).build())
        ).build()
        client.queryProductDetailsAsync(request) { result, response ->
            if (result.responseCode != BillingClient.BillingResponseCode.OK) return@queryProductDetailsAsync
            details = response.productDetailsList.firstOrNull()
            offers.value = details?.subscriptionOfferDetails.orEmpty()
                .filter { it.basePlanId in setOf("monthly", "annual") }
                .mapNotNull { offer ->
                    val price = offer.pricingPhases.pricingPhaseList.lastOrNull()?.formattedPrice
                        ?: return@mapNotNull null
                    PremiumOffer(offer.basePlanId,
                        if (offer.basePlanId == "annual") "Yearly" else "Monthly",
                        price, offer.offerToken)
                }.distinctBy { it.basePlanId }
            billingAvailable.value = verifierReady && offers.value.isNotEmpty()
            message.value = if (billingAvailable.value) "Google Play prices are shown above."
                else "No active Premium subscription plans were found in Google Play."
        }
    }

    fun purchase(basePlan: String) {
        if (!billingAvailable.value || !verifierReady) return
        val offer = offers.value.firstOrNull { it.basePlanId == basePlan } ?: return
        val product = details ?: return
        val item = BillingFlowParams.ProductDetailsParams.newBuilder()
            .setProductDetails(product).setOfferToken(offer.offerToken).build()
        val result = client.launchBillingFlow(activity,
            BillingFlowParams.newBuilder().setProductDetailsParamsList(listOf(item)).build())
        if (result.responseCode != BillingClient.BillingResponseCode.OK)
            message.value = "Could not open Google Play checkout: " + result.debugMessage
    }

    override fun onPurchasesUpdated(result: BillingResult, purchases: MutableList<Purchase>?) {
        when (result.responseCode) {
            BillingClient.BillingResponseCode.OK -> purchases.orEmpty().forEach(::verify)
            BillingClient.BillingResponseCode.USER_CANCELED ->
                message.value = "Purchase cancelled. No charge was completed."
            else -> message.value = "Google Play purchase status: " + result.debugMessage
        }
    }

    fun restorePurchases() {
        if (!verifierReady || !client.isReady) return
        val params = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.SUBS).build()
        client.queryPurchasesAsync(params) { result, purchases ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                if (purchases.none { it.products.contains("readaloud_premium") }) {
                    VerifiedPlayEntitlement.revoke()
                    controller.refreshVerifiedPremiumStatus()
                } else purchases.filter { it.products.contains("readaloud_premium") }
                    .forEach(::verify)
            }
        }
    }

    private fun verify(purchase: Purchase) {
        if (!purchase.products.contains("readaloud_premium")) return
        if (purchase.purchaseState != Purchase.PurchaseState.PURCHASED) {
            message.value = "Subscription payment is pending. Premium stays locked until completed."
            return
        }
        scope.launch {
            val verifiedExpiry = withContext(Dispatchers.IO) {
                verifyOnServer(purchase.purchaseToken)
            }
            if (verifiedExpiry > System.currentTimeMillis()) {
                // Keep premium functional during long background listening,
                // and never grant access beyond server-confirmed expiry.
                val ttl = ((verifiedExpiry - System.currentTimeMillis()) / 1000L)
                    .coerceIn(1L, 6L * 60L * 60L)
                VerifiedPlayEntitlement.setVerifiedFor(ttl)
                controller.refreshVerifiedPremiumStatus()
                message.value = "Premium subscription verified. Unlimited background listening enabled."
                if (!purchase.isAcknowledged) {
                    client.acknowledgePurchase(
                        AcknowledgePurchaseParams.newBuilder()
                            .setPurchaseToken(purchase.purchaseToken).build()
                    ) { result ->
                        if (result.responseCode != BillingClient.BillingResponseCode.OK)
                            message.value = "Premium verified; Google Play acknowledgement needs retry."
                    }
                }
            } else {
                VerifiedPlayEntitlement.revoke()
                controller.refreshVerifiedPremiumStatus()
                message.value = "Subscription was not verified. Premium remains locked."
            }
        }
    }

    private fun verifyOnServer(token: String): Long = try {
        if (!verifierReady || token.isBlank()) return 0L
        val connection = URL(BuildConfig.BILLING_VERIFIER_URL).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "POST"
            connection.connectTimeout = 12_000
            connection.readTimeout = 12_000
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.outputStream.use {
                it.write(JSONObject().put("packageName", activity.packageName)
                    .put("productId", "readaloud_premium")
                    .put("purchaseToken", token).toString().toByteArray(Charsets.UTF_8))
            }
            if (connection.responseCode != 200) return 0L
            val payload = connection.inputStream.bufferedReader().use { it.readText().take(8192) }
            val result = JSONObject(payload)
            if (result.optBoolean("verified", false) &&
                result.optString("productId") == "readaloud_premium")
                result.optLong("expiresAtMillis", 0L) else 0L
        } finally { connection.disconnect() }
    } catch (_: Exception) { 0L }

    fun close() { client.endConnection() }
}
