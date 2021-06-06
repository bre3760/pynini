#include <FS.h> //this needs to be first
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <string.h>
#include <typeinfo>

struct Config {
  char catalog_ip[12];
  int port;
};
Config config;                         // <- global configuration object

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  // init values from file system
  if(!SPIFFS.begin()){
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
  if (SPIFFS.begin()) {
    Serial.println("mounted file system");

    File jsonFile = SPIFFS.open("/config.json", "r");
    if(!jsonFile){
      Serial.println("Failed to open file for reading");
      return;
    } else {
      Serial.println("OPENED FILE");
      String debugLogData;
      while (jsonFile.available()){
        debugLogData += char(jsonFile.read());
      }

      StaticJsonDocument<512> doc;

      // Deserialize the JSON document
      DeserializationError error = deserializeJson(doc, jsonFile);
      if (error)
        Serial.println(F("Failed to read file, using default configuration"));
    
      // Copy values from the JsonDocument to the Config
      config.port = doc["port"] | 2731;
      strlcpy(config.catalog_ip,                  // <- destination
              doc["catalog_ip"] | "0.0.0.0",      // <- source
              sizeof(config.catalog_ip));         // <- destination's capacity
    
      // Close the file (Curiously, File's destructor doesn't close the file)
      jsonFile.close();
           
      Serial.println("=====================================");
      Serial.println("data from file");
      Serial.println(debugLogData);
      Serial.println("=====================================");


      Serial.println("=====================================");
      Serial.println("data from config after reading file with arduinojson");
      Serial.println(config.catalog_ip);
      Serial.println("=====================================");
 



      
    }
  }
}

void loop(){
  Serial.println("hi");
  delay(7000);
}
