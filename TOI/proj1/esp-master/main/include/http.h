/* Constants that aren't configurable in menuconfig */
// #define WEB_SERVER "enzodras15oqzy7.m.pipedream.net"
#define WEB_SERVER "192.168.0.145"
#define WEB_PORT "5000"
#define WEB_PATH "/sensor_data"

void http_get_task(void *pvParameters);
