#include <string.h>
#include "include/http.h"
#include "include/temp.h"
#include "include/lum.h"
#include "include/measures.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"

#include "nvs_flash.h"
#include "esp_log.h"
#include "esp_now.h"
#include "esp_wifi.h"

static EventGroupHandle_t wifi_event_group;
const int CONNECTED_BIT = BIT0;

static const char *TAG_NOW = "ESP_NOW";
static const char *TAG = "MAIN";
static const char *AP_SSID = "my esp3";
static const char *AP_PASSWORD = "secretpwd";
static struct measures m[2];

void on_data_recv(const uint8_t *mac, const uint8_t *incomingData, int len) {
    struct measures m_remote;
    memcpy(&m_remote, incomingData, sizeof(m_remote));
    m[1] = m_remote;
    ESP_LOGI(TAG_NOW, "Received data from %d", *mac);
}

static void event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        esp_wifi_connect();
        xEventGroupClearBits(wifi_event_group, CONNECTED_BIT);
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(wifi_event_group, CONNECTED_BIT);
    }
}

static void initialise_wifi(void)
{
        ESP_ERROR_CHECK(esp_netif_init());
        wifi_event_group = xEventGroupCreate();
        ESP_ERROR_CHECK(esp_event_loop_create_default());
        esp_netif_t *ap_netif = esp_netif_create_default_wifi_ap();
        assert(ap_netif);
        esp_netif_t *sta_netif = esp_netif_create_default_wifi_sta();
        assert(sta_netif);
        wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
        ESP_ERROR_CHECK( esp_wifi_init(&cfg) );
        ESP_ERROR_CHECK( esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_DISCONNECTED, &event_handler, NULL) );
        ESP_ERROR_CHECK( esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL) );

        ESP_ERROR_CHECK( esp_wifi_set_storage(WIFI_STORAGE_RAM));
        ESP_ERROR_CHECK( esp_wifi_set_mode(WIFI_MODE_NULL) );
        ESP_ERROR_CHECK( esp_wifi_start() );
}

static bool wifi_apsta(int timeout_ms)
{
        wifi_config_t ap_config = { 0 };
        strcpy((char *)ap_config.ap.ssid,AP_SSID);
        strcpy((char *)ap_config.ap.password, AP_PASSWORD);
        ap_config.ap.authmode = WIFI_AUTH_WPA_WPA2_PSK;
        ap_config.ap.ssid_len = strlen(AP_SSID);
        ap_config.ap.max_connection = 4;
        ap_config.ap.channel = 5;

        wifi_config_t sta_config = { 0 };
        strcpy((char *)sta_config.sta.ssid, CONFIG_ESP_WIFI_SSID);
        strcpy((char *)sta_config.sta.password, CONFIG_ESP_WIFI_PASSWORD);


        ESP_ERROR_CHECK( esp_wifi_set_mode(WIFI_MODE_APSTA) );
        ESP_ERROR_CHECK( esp_wifi_set_config(ESP_IF_WIFI_AP, &ap_config) );
        ESP_ERROR_CHECK( esp_wifi_set_config(ESP_IF_WIFI_STA, &sta_config) );
        ESP_ERROR_CHECK( esp_wifi_start() );
        ESP_LOGI(TAG, "Starting softAP");

        ESP_ERROR_CHECK( esp_wifi_connect() );
        int bits = xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT, pdFALSE, pdTRUE, timeout_ms / portTICK_PERIOD_MS);
        return (bits & CONNECTED_BIT) != 0;
}

void app_main(void)
{
    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    initialise_wifi();
    wifi_apsta(300000);

    ret = esp_now_init();
    ESP_ERROR_CHECK(ret);

    esp_now_register_recv_cb(on_data_recv);

    // xTaskCreate(&lum_task, "lum_task", configMINIMAL_STACK_SIZE * 4, &m, 5, NULL);
    // xTaskCreate(&ds18x20_test, "ds18x20_test", configMINIMAL_STACK_SIZE * 4, &m, 5, NULL);
    xTaskCreate(&http_get_task, "http_get_task", 4096, &m, 5, NULL);
}