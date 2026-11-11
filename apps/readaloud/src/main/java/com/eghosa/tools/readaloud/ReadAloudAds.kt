package com.eghosa.tools.readaloud

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.runtime.mutableStateOf
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.AdSize
import com.google.android.gms.ads.AdView
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.FullScreenContentCallback
import com.google.android.gms.ads.rewarded.RewardedAd
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback
import com.google.android.ump.ConsentInformation
import com.google.android.ump.ConsentRequestParameters
import com.google.android.ump.UserMessagingPlatform
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/** GDPR/UMP gate. Only Google demo ads are ever used in debug builds. */
class ReadAloudAds(private val activity: ComponentActivity) {
    val canRequestAds = mutableStateOf(false)
    val rewardReady = mutableStateOf(false)
    val privacyOptionsRequired = mutableStateOf(false)
    private val consent = UserMessagingPlatform.getConsentInformation(activity)
    private var initialized = false
    private var reward: RewardedAd? = null
    private var rewardLoading = false

    fun requestConsent() {
        if (!BuildConfig.ADS_ENABLED) return
        consent.requestConsentInfoUpdate(activity,
            ConsentRequestParameters.Builder().build(),
            {
                privacyOptionsRequired.value = consent.privacyOptionsRequirementStatus ==
                    ConsentInformation.PrivacyOptionsRequirementStatus.REQUIRED
                UserMessagingPlatform.loadAndShowConsentFormIfRequired(activity) {
                    startAdsIfAllowed()
                }
                // A previous valid consent may already permit requests.
                startAdsIfAllowed()
            }, {
                // Use only a previously valid consent state after a connectivity error.
                startAdsIfAllowed()
            })
    }

    private fun startAdsIfAllowed() {
        if (!BuildConfig.ADS_ENABLED || !consent.canRequestAds()) return
        if (initialized) return
        initialized = true
        canRequestAds.value = true
        CoroutineScope(Dispatchers.IO).launch {
            MobileAds.initialize(activity.applicationContext) {
                activity.runOnUiThread { loadReward() }
            }
        }
    }

    fun loadReward() {
        if (!canRequestAds.value || rewardLoading || reward != null) return
        rewardLoading = true
        RewardedAd.load(activity, BuildConfig.ADS_REWARD_UNIT, AdRequest.Builder().build(),
            object : RewardedAdLoadCallback() {
                override fun onAdLoaded(ad: RewardedAd) {
                    rewardLoading = false
                    reward = ad
                    rewardReady.value = true
                }
                override fun onAdFailedToLoad(error: LoadAdError) {
                    rewardLoading = false
                    rewardReady.value = false
                    reward = null
                }
            })
    }

    fun showRewarded(onRewardEarned: () -> Unit) {
        val ad = reward ?: return
        reward = null
        rewardReady.value = false
        var granted = false
        ad.fullScreenContentCallback = object : FullScreenContentCallback() {
            override fun onAdDismissedFullScreenContent() { loadReward() }
            override fun onAdFailedToShowFullScreenContent(adError: com.google.android.gms.ads.AdError) {
                loadReward()
            }
        }
        ad.show(activity) {
            if (!granted) {
                granted = true
                onRewardEarned()
            }
        }
    }

    fun showPrivacyOptions() {
        if (privacyOptionsRequired.value) {
            UserMessagingPlatform.showPrivacyOptionsForm(activity) {
                canRequestAds.value = consent.canRequestAds()
                privacyOptionsRequired.value = consent.privacyOptionsRequirementStatus ==
                    ConsentInformation.PrivacyOptionsRequirementStatus.REQUIRED
            }
        }
    }
}

/** Banners never appear inside the spoken passage, and are absent for Premium. */
@Composable
fun ReadAloudBanner(coordinator: ReadAloudAds) {
    if (!coordinator.canRequestAds.value || !BuildConfig.ADS_ENABLED) return
    val context = LocalContext.current
    val banner = remember {
        AdView(context).apply {
            adUnitId = BuildConfig.ADS_BANNER_UNIT
            setAdSize(AdSize.BANNER)
            loadAd(AdRequest.Builder().build())
        }
    }
    DisposableEffect(banner) { onDispose { banner.destroy() } }
    Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
        AndroidView(factory = { banner })
    }
}
