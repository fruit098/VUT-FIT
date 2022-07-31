#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <ds18x20.h>
#include <esp_log.h>
#include <esp_err.h>

#include "include/measures.h"

static const gpio_num_t SENSOR_GPIO = CONFIG_TEMP_ONEWIRE_GPIO;
static const int MAX_SENSORS = CONFIG_TEMP_DS18X20_MAX_SENSORS;
static const int RESCAN_INTERVAL = 8;
static const uint32_t LOOP_DELAY_MS = 1000;

static const char *TAG = "TEMP";

void ds18x20_test(void *pvParameter)
{
    ds18x20_addr_t addrs[MAX_SENSORS];
    float temps[MAX_SENSORS];
    size_t sensor_count = 0;
    struct measures *m = pvParameter;
    gpio_set_pull_mode(SENSOR_GPIO, GPIO_PULLUP_ONLY);

    esp_err_t res;
    while (1)
    {
        res = ds18x20_scan_devices(SENSOR_GPIO, addrs, MAX_SENSORS, &sensor_count);
        if (res != ESP_OK)
        {
            ESP_LOGE(TAG, "Sensors scan error %d (%s)", res, esp_err_to_name(res));
            continue;
        }

        if (!sensor_count)
        {
            ESP_LOGW(TAG, "No sensors detected!");
            continue;
        }

        if (sensor_count > MAX_SENSORS)
            sensor_count = MAX_SENSORS;

        for (int i = 0; i < RESCAN_INTERVAL; i++)
        {
            res = ds18x20_measure_and_read_multi(SENSOR_GPIO, addrs, sensor_count, temps);
            if (res != ESP_OK)
            {
                ESP_LOGE(TAG, "Sensors read error %d (%s)", res, esp_err_to_name(res));
                continue;
            }

            for (int j = 0; j < sensor_count; j++)
            {
                float temp_c = temps[j];
                m[0].temp = temp_c;
                float temp_f = (temp_c * 1.8) + 32;
            }
            vTaskDelay(pdMS_TO_TICKS(LOOP_DELAY_MS));
        }
    }
}


