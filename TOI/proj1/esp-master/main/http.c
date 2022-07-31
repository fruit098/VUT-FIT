#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/dns.h"

#include "include/http.h"
#include "include/measures.h"

const char *BODY =  "{\"data\": [{\"name\": \"esp1\",\"temperature\": %.2f,\"brightness\": %d},{\"name\": \"esp2\",\"temperature\": %.2f,\"brightness\": %d}]}";

static const char *HEADER = "POST " WEB_PATH " HTTP/1.0\r\n"
    "Host: "WEB_SERVER":"WEB_PORT"\r\n"
    "User-Agent: esp-idf/1.0 esp32\r\n"
    "Content-Type: application/json\r\n"
    "Content-Length: %d\r\n"
    "\r\n" ;

static const char *HTTP_TAG = "HTTP";
static const int LOOP_DELAY_MS = 5000;
static const int SLEEP_IN_SEC = 5;

void http_get_task(void *pvParameters)
{
    struct measures *m = pvParameters;
    const struct addrinfo hints = {
        .ai_family = AF_INET,
        .ai_socktype = SOCK_STREAM,
    };
    struct addrinfo *res;
    struct in_addr *addr;
    int s, r;
    char recv_buf[64];

    while (1)
    {
        int err = getaddrinfo(WEB_SERVER, WEB_PORT, &hints, &res);
        if(err != 0 || res == NULL) {
            ESP_LOGE(HTTP_TAG, "DNS lookup failed err=%d res=%p", err, res);
            vTaskDelay(1000 / portTICK_PERIOD_MS);
        } else {
            break;
        }
    }
    
    /* Code to print the resolved IP.
        Note: inet_ntoa is non-reentrant, look at ipaddr_ntoa_r for "real" code */
    addr = &((struct sockaddr_in *)res->ai_addr)->sin_addr;
    ESP_LOGI(HTTP_TAG, "DNS lookup succeeded. IP=%s", inet_ntoa(*addr));

    while(1) {
        ESP_LOGI(HTTP_TAG, "Waiting for %ds", SLEEP_IN_SEC);
        vTaskDelay(pdMS_TO_TICKS(LOOP_DELAY_MS));
        s = socket(res->ai_family, res->ai_socktype, 0);
        if(s < 0) {
            ESP_LOGE(HTTP_TAG, "... Failed to allocate socket.");
            freeaddrinfo(res);
            vTaskDelay(1000 / portTICK_PERIOD_MS);
            continue;
        }

        if(connect(s, res->ai_addr, res->ai_addrlen) != 0) {
            ESP_LOGE(HTTP_TAG, "... socket connect failed errno=%d", errno);
            close(s);
            freeaddrinfo(res);
            vTaskDelay(4000 / portTICK_PERIOD_MS);
            continue;
        }

        char BODY_BUFFER[200];
        memset(BODY_BUFFER, '\0', 200);
        char HEADER_BUFFER[200];
        memset(HEADER_BUFFER, '\0', 200);
        char REQUEST[400];
        memset(REQUEST, '\0', 400);

        ESP_LOGI(HTTP_TAG, "Temperature from HTTP: %f|%f", m[0].temp, m[1].temp);
        ESP_LOGI(HTTP_TAG, "Luminescence from HTTP: %d|%d", m[0].lum, m[1].lum);
        sprintf(BODY_BUFFER,BODY, m[0].temp, m[0].lum, m[1].temp, m[1].lum);
        sprintf(REQUEST, HEADER, strlen(BODY_BUFFER));
        strcat(REQUEST, BODY_BUFFER);

        if (write(s, REQUEST, strlen(REQUEST)) < 0) {
            ESP_LOGE(HTTP_TAG, "... socket send failed");
            close(s);
            vTaskDelay(4000 / portTICK_PERIOD_MS);
            continue;
        }

        struct timeval receiving_timeout;
        receiving_timeout.tv_sec = 5;
        receiving_timeout.tv_usec = 0;
        if (setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &receiving_timeout,
                sizeof(receiving_timeout)) < 0) {
            ESP_LOGE(HTTP_TAG, "... failed to set socket receiving timeout");
            close(s);
            vTaskDelay(4000 / portTICK_PERIOD_MS);
            continue;
        }

        /* Read HTTP response */
        do {
            bzero(recv_buf, sizeof(recv_buf));
            r = read(s, recv_buf, sizeof(recv_buf)-1);
            // for(int i = 0; i < r; i++) {
            //     putchar(recv_buf[i]);
            // }
        } while(r > 0);
        close(s);
    }
    freeaddrinfo(res);
}

