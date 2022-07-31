#include <string.h>
#include "include/temp.h"
#include "include/lum.h"
#include "include/measures.h"
#include "include/wifi.h"

#include "nvs_flash.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "esp_now.h"
#include "esp_event.h"
#include "esp_wifi.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"

static const char *TAG = "MAIN";
uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
static EventGroupHandle_t s_evt_group;
struct measures m;
esp_now_peer_info_t peerInfo;

static void packet_sent_cb(const uint8_t *mac_addr, esp_now_send_status_t status)
{
    if (mac_addr == NULL) {
        ESP_LOGE(TAG, "Send cb arg error");
        return;
    }

    assert(status == ESP_NOW_SEND_SUCCESS || status == ESP_NOW_SEND_FAIL);
    xEventGroupSetBits(s_evt_group, BIT(status));
}
 
esp_err_t send_espnow_data() {
    esp_err_t ret = esp_now_send(broadcastAddress, (uint8_t *) &m, sizeof(m));
    if (ret != ESP_OK) {
        ESP_ERROR_CHECK( ret );
    }

    EventBits_t bits = xEventGroupWaitBits(s_evt_group, BIT(ESP_NOW_SEND_SUCCESS) | BIT(ESP_NOW_SEND_FAIL), pdTRUE, pdFALSE, 2000 / portTICK_PERIOD_MS);
    if ( !(bits & BIT(ESP_NOW_SEND_SUCCESS)) )
    {
        if (bits & BIT(ESP_NOW_SEND_FAIL))
        {
            ESP_LOGE(TAG, "Send error");
            return ESP_FAIL;
        }
        ESP_LOGE(TAG, "Send timed out");
        return ESP_ERR_TIMEOUT;
    }

    ESP_LOGI(TAG, "Sent!");
    return ESP_OK;
}

void app_main(void)
{
    m.temp = 0.0;
    m.lum = 0;
    s_evt_group = xEventGroupCreate();
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    wifi_init_sta();

    ESP_ERROR_CHECK( esp_now_init() );
    ESP_ERROR_CHECK( esp_now_register_send_cb(packet_sent_cb) );

    peerInfo.channel = 0;  
    peerInfo.encrypt = false;
    peerInfo.ifidx = ESP_IF_WIFI_STA;
    memcpy(peerInfo.peer_addr, broadcastAddress, ESP_NOW_ETH_ALEN);

    ESP_ERROR_CHECK(esp_now_add_peer(&peerInfo));

    m.lum = lum_task();
    m.temp = ds18x20();

    send_espnow_data();
    esp_now_deinit();
    esp_wifi_stop();
    esp_deep_sleep(1000 * 5000);
}