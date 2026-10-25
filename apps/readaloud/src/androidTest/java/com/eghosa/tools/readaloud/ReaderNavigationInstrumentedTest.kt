package com.eghosa.tools.readaloud

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ReaderNavigationInstrumentedTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun majorReaderScreensAreReachable() {
        compose.onNodeWithText("Read and listen, right on your phone").assertExists()
        compose.onNodeWithText("Library").performClick()
        compose.onNodeWithText("Saved on this phone").assertExists()
        compose.onNodeWithText("Voices").performClick()
        compose.onNodeWithText("Choose your speech engine").assertExists()
        compose.onNodeWithText("Settings").performClick()
        compose.onNodeWithText("Private by design").assertExists()
        compose.onNodeWithText("Read").performClick()
        compose.onNodeWithText("Your document").assertExists()
        compose.onNodeWithText("Reading text size", substring = true).assertExists()
        compose.onNodeWithText("Sleep timer").assertExists()
    }
}
