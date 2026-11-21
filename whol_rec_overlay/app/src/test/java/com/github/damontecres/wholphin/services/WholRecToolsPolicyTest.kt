package com.github.damontecres.wholphin.services

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WholRecToolsPolicyTest {
    @Test
    fun guideRefreshUsesExactJellyfinScheduledTaskKey() {
        assertTrue(isGuideTask("RefreshGuide"))
        assertTrue(isGuideTask("refreshguide"))
        assertFalse(isGuideTask("RefreshLibrary"))
        assertFalse(isGuideTask("NotRefreshGuide"))
    }

    @Test
    fun iptvBridgeRequiresHttpOrHttpsHostWithoutCredentialsInAuthority() {
        assertTrue(validWebhookUrl("https://nas.local/hooks/iptv"))
        assertTrue(validWebhookUrl("http://192.168.1.2:8123/api/webhook/iptv-test"))
        assertFalse(validWebhookUrl(""))
        assertFalse(validWebhookUrl("file:///etc/passwd"))
        assertFalse(validWebhookUrl("https://user:password@nas.local/refresh"))
        assertFalse(validWebhookUrl("https://nas.local/refresh#fragment"))
        assertFalse(validWebhookUrl("javascript:alert(1)"))
    }
}
