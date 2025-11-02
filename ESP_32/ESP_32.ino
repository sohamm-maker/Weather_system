#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// wifi 
const char* ssid = "Ronits_phone";
const char* password = "hotspott";

// server id
const char* serverURL = "http://10.43.232.8:5000/api/data";  // Adjust to your PC IP

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    // Create random test data
    float temperature = random(200, 350) / 10.0;   // 20.0 - 35.0 °C
    float humidity = random(400, 900) / 10.0;      // 40% - 90%
    float pressure = random(9900, 10400) / 10.0;   // 990 - 1040 hPa
    int air_quality = random(10, 200);              // arbitrary AQI value
    float wind_speed = random(0, 200) / 10.0;       // 0 - 20 km/h
    float wind_direction = random(0, 360);          // 0° - 359°
    float rainfall = random(0, 50) / 10.0;         // 0 - 5.0 mm

    // Build JSON document
    DynamicJsonDocument doc(256);
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
    doc["pressure"] = pressure;
    doc["air_quality"] = air_quality;
    doc["wind_speed"] = wind_speed;
    doc["wind_direction"] = wind_direction;
    doc["rainfall"] = rainfall;

    String json;
    serializeJson(doc, json);

    // Send POST request
    int code = http.POST(json);
    Serial.printf("Data sent. HTTP Response code: %d\n", code);
    Serial.println(json);

    http.end();
  } else {
    Serial.println("WiFi disconnected. Reconnecting...");
    WiFi.begin(ssid, password);
  }

  delay(30000); // sends data every 30 seconds
}
