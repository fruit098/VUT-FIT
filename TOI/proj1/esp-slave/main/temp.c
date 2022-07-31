#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <ds18x20.h>
#include <esp_log.h>
#include <esp_err.h>

#include "include/measures.h"

static const gpio_num_t SENSOR_GPIO = CONFIG_TEMP_ONEWIRE_GPIO;
static const int MAX_SENSORS = CONFIG_TEMP_DS18X20_MAX_SENSORS;

static const char *TAG = "TEMP";

float ds18x20()
{
    float retval = 0.0;
    ds18x20_addr_t addrs[MAX_SENSORS];
    float temps[MAX_SENSORS];
    size_t sensor_count = 0;
    gpio_set_pull_mode(SENSOR_GPIO, GPIO_PULLUP_ONLY);

    esp_err_t res;
    res = ds18x20_scan_devices(SENSOR_GPIO, addrs, MAX_SENSORS, &sensor_count);
    if (res != ESP_OK)
    {
        ESP_LOGE(TAG, "Sensors scan error %d (%s)", res, esp_err_to_name(res));
        return 0.0;
    }

    if (!sensor_count)
    {
        ESP_LOGW(TAG, "No sensors detected!");
        return 0.0;
    }
    if (sensor_count > MAX_SENSORS)
        sensor_count = MAX_SENSORS;

    res = ds18x20_measure_and_read_multi(SENSOR_GPIO, addrs, sensor_count, temps);
    if (res != ESP_OK)
    {
        ESP_LOGE(TAG, "Sensors read error %d (%s)", res, esp_err_to_name(res));
        return 0.0;
    }

    for (int j = 0; j < sensor_count; j++)
    {
        float temp_c = temps[j];
        retval = temp_c;
        float temp_f = (temp_c * 1.8) + 32;
        ESP_LOGI(TAG, "Sensor %08x%08x (%s) reports %.3f°C (%.3f°F)",
                (uint32_t)(addrs[j] >> 32), (uint32_t)addrs[j],
                (addrs[j] & 0xff) == DS18B20_FAMILY_ID ? "DS18B20" : "DS18S20",
                temp_c, temp_f);
    }
    return retval;
}
