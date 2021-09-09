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

// function prototypes
void connectWifi();
int  httpConnect(char*, char*, char*);
void LightsOn(int actuatorPin);
void LightsOff(int actuatorPin);
void callback(char* topic, byte* message, unsigned int length);

// wifi variables and constants
struct WifiConfig {
  char ssid[8];
  char password[17];
};
WifiConfig wifi_config;                         // <- global configuration object

boolean wifiConnected = false;
String local_ip;

// Wire connection
const int relayPin1 = 5;                        //I am using ESP8266 EPS-12F GPIO5 and GPIO4
const int relayPin2 = 4;
int breadType;

// mqtt configuration 
struct MQTTConfig {
  char mqtt_server[12];
  int  mqtt_port;
  char mqtt_username[8]; 
  char mqtt_password[7]; 
  char clientID[12]; 
  char topic[11];
  char caseID[5];
};
MQTTConfig mqtt_config;                          // <- global configuration object

char breadTopic[10];                             // initialization for topics 
char fanTopic[11];
char lampTopic[12];


// http config
struct HttpConfig {
  char rpi_ip[12];
  char rpi_port[5];
  char dockerCatalogIp[13];
  char dockerCatalogPort[5];
  char httpCaseID[5];
};
HttpConfig http_config;

// Creation of an ESP8266WiFi object
WiFiClient espClient;
// Creation of a PubSubClient object
PubSubClient client(espClient);

// NTP CURRENT TIME
String currentHour = "";
String currentMinute = "";
String currentSeconds = "";
String currentDate = "";
int currentYear;
int currentMonth;
int monthDay;
const long utcOffsetInSeconds = 0; // rome time zone
char daysOfTheWeek[7][12] = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};

// Define NTP Client to get time
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", utcOffsetInSeconds);


void setup() {
  
  Serial.begin(115200);

  // init values from file system
  if(!SPIFFS.begin()){
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
  if (SPIFFS.begin()) {
    Serial.println("mounted file system");
    // open config file 
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
      Serial.println("=====================================");
      Serial.println("data from file");
      Serial.println(debugLogData);
      Serial.println("=====================================");


      Serial.println("Proceding with value extraction");
      StaticJsonDocument<1024> doc;
      // Deserialize the JSON document
      DeserializationError error = deserializeJson(doc, debugLogData);
      if (error){
        Serial.println("Failed to read file, using default configuration");
      } else {
        // Copy values from the JsonDocument to the Config
        // WIFI CONFIG
        strlcpy(wifi_config.ssid,                  
                doc["wifi_ssid"] | "McLovin",     
                sizeof(wifi_config.ssid));         
        strlcpy(wifi_config.password,                           // <- destination
                doc["wifi_password"] | "1234567890000000",      // <- source
                sizeof(wifi_config.password));                  // <- destination's capacity
        //MQTT CONFIG
        strlcpy(mqtt_config.mqtt_server,                  
                doc["mqtt_server"] | "0.0.0.0",     
                sizeof(mqtt_config.mqtt_server));
        mqtt_config.mqtt_port = doc["mqtt_port"] | 1883;      
        strlcpy(mqtt_config.mqtt_username,                  
                doc["mqtt_username"] | "brendan",     
                sizeof(mqtt_config.mqtt_username));
        strlcpy(mqtt_config.mqtt_password,                  
                doc["mqtt_password"] | "pynini",     
                sizeof(mqtt_config.mqtt_password));
        strlcpy(mqtt_config.clientID,                  
                doc["clientID"] | "esp-arduino",     
                sizeof(mqtt_config.clientID));
        strlcpy(mqtt_config.caseID,                  
                doc["caseID"] | "CCC2",     
                sizeof(mqtt_config.caseID));
        //HTTP CONFIG
        strlcpy(http_config.rpi_ip,                  
                doc["rpi_ip"] | "192.168.1.4",     
                sizeof(http_config.rpi_ip));
        strlcpy(http_config.rpi_port,                  
                doc["rpi_port"] | "9090",     
                sizeof(http_config.rpi_port));
        strlcpy(http_config.dockerCatalogIp,                  
                doc["catalog_ip"] | "192.168.1.14",     
                sizeof(http_config.dockerCatalogIp));
        strlcpy(http_config.dockerCatalogPort,                  
                doc["catalog_port"] | "9090",     
                sizeof(http_config.dockerCatalogPort));
        strlcpy(http_config.httpCaseID,                  
                doc["caseID"] | "CCC2",     
                sizeof(http_config.httpCaseID));
      }
      // Close the file (Curiously, File's destructor doesn't close the file)
      jsonFile.close();      
    }
  }

  connectWifi();                           // Initialise wifi connection
  int got_topics = 0;

  // could add while got_topics != 1 
  while (got_topics != 1) {
    got_topics = httpConnect(breadTopic,fanTopic,lampTopic);     // send post request to catalog 
 
    delay(7000);
  }
  
  delay(7000);
  Serial.println("got_topics value: ");
  Serial.println(got_topics);
  
  client.setServer(mqtt_config.mqtt_server, mqtt_config.mqtt_port);
  client.setCallback(callback);            // create callback function for mqtt
  char buf_lamp[17];
  const char *first_lamp = mqtt_config.caseID;
  const char *second_lamp = "/trigger/lamp";
  strcpy(buf_lamp,first_lamp);
  strcat(buf_lamp,second_lamp);

  char buf_fan[17];
  const char *first_fan = mqtt_config.caseID;
  const char *second_fan = "/trigger/fan";
  strcpy(buf_fan,first_fan);
  strcat(buf_fan,second_fan);

  Serial.println("SUBSCRIBING TO: ");
  Serial.println(buf_lamp);
  Serial.println(buf_fan);

  client.subscribe(buf_lamp);
  client.subscribe(buf_fan);
  
  Wire.begin(D1, D2);                      // join i2c bus with SDA=D1 and SCL=D2 of NodeMC  
}

void loop() {
  
  if (!client.connected()) {               // reconnecting to broker 
    reconnect();
  }
  client.loop();

  breadType = Wire.requestFrom(8,1);       // ask on line/bus 8 for 30 bits, then read while the wire gets data
  String breadData="";
  while(Wire.available()){
    char c = Wire.read();
    breadData += c;
  }
  Serial.print("The Bread type from button is: ");
  Serial.print(breadData);
  Serial.print("\n");

  timeClient.update();     // updating current time
  unsigned long epochTime = timeClient.getEpochTime();
  struct tm *ptm = gmtime ((time_t *)&epochTime);
  currentHour = timeClient.getHours();
  currentMinute = timeClient.getMinutes();
  currentSeconds = timeClient.getSeconds();
  monthDay = ptm->tm_mday;
  currentMonth =ptm->tm_mon+1;
  currentYear = ptm->tm_year+1900;
  currentDate = String(currentYear) + "-" + String(currentMonth) + "-" + String(monthDay);
  String currentTime = currentHour + ":" + currentMinute + ":" + currentSeconds;
  String currentDateTime = currentDate + " " + currentTime;

  String messageDescription = "bread_index" ;
  String payload = "{";
  payload +=  '"';
  payload+= "timestamp";
  payload+= '"';
  payload += ":";
  payload+='"';
  payload+= currentDateTime;
  payload+='"';
  payload += ",";
  payload +=  '"';
  payload+= "caseID";
  payload+= '"';
  payload += ":";
  payload+='"';
  payload+= mqtt_config.caseID;
  payload+='"';
  payload += ",";
  payload +=  '"';
  payload+= messageDescription;
  payload+= '"';
  payload += ":";
  payload+='"';
  payload+= breadData;
  payload+='"';
  payload += "}";

  Serial.println("The payload is: ");
  Serial.println(payload);
  Serial.print("\n");

  char buf_bread[15];
  const char *first_bread = mqtt_config.caseID;
  const char *forwardslash = "/";
  const char *second_bread = breadTopic;
  strcpy(buf_bread,first_bread);
  strcat(buf_bread,forwardslash);
  strcat(buf_bread,second_bread);

  if( client.publish(buf_bread, payload.c_str()) ){
        Serial.println("Message sent with mqtt");
    } else {
        Serial.print("Failed to send");
    }

  delay(125*60); // every 15 seconds
  
}

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//      Arduino Uno Switch on / off
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
void LightsOn(int actuatorPin) {
      Serial.print("Switch turn on\n");
      Wire.beginTransmission(8); /* begin with device address 8 */
      if(actuatorPin == 13){
        Wire.write("{\"gpio\":13,\"state\":1}");  
      }
      if(actuatorPin == 12){
        Wire.write("{\"gpio\":12,\"state\":1}");  
      }
      Wire.endTransmission();    /* stop transmitting */
}

void LightsOff(int actuatorPin) {
    Serial.print("Switch turn off \n");
    Wire.beginTransmission(8); /* begin with device address 8 */

    if(actuatorPin == 13){
        Wire.write("{\"gpio\":13,\"state\":0}");  
      }
      if(actuatorPin == 12){
        Wire.write("{\"gpio\":12,\"state\":0}");  
      } 
    Wire.endTransmission();    /* stop transmitting */
}

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//      HTTP CONNECTION
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

int httpConnect(char*, char*, char*)
  {
    timeClient.begin();     // NTP time
    timeClient.update();     // updating current time
    unsigned long epochTime = timeClient.getEpochTime();
    struct tm *ptm = gmtime ((time_t *)&epochTime);
    currentHour = timeClient.getHours();
    currentMinute = timeClient.getMinutes();
    currentSeconds = timeClient.getSeconds();
    
    monthDay = ptm->tm_mday;
    currentMonth =ptm->tm_mon+1;
    currentYear = ptm->tm_year+1900;
    currentDate = String(currentYear) + "-" + String(currentMonth) + "-" + String(monthDay);
    int postDone=0;
    if ((WiFi.status() == WL_CONNECTED)) {
      HTTPClient http; 
      DynamicJsonDocument doc(1024);    
      doc["name"] = "arduino";
      doc["ip"] = local_ip;
      doc["port"] = "8080";
      doc["last_seen"] = currentDate  + " " + currentHour + ":" + currentMinute + ":" + currentSeconds;
      doc["dev_name"] = "arduino";
      doc["caseID"] = http_config.httpCaseID;
      doc["sensorID"] = "arduino";
      String jsonData;
      serializeJson(doc,jsonData);
      int httpCode;
      String urlForPost = "http://" + String(http_config.dockerCatalogIp) + ":"+ String(http_config.dockerCatalogPort) + "/addSensor";
      Serial.println("urlForPost used is: ");
      Serial.println(urlForPost);
      http.useHTTP10(true);
      http.begin(espClient,urlForPost); 
      http.addHeader("Content-Type", "application/json");
      httpCode = http.POST(jsonData);        // code response of the POST request
      Serial.print("HTTP response code: ");
      Serial.println(httpCode);

      if (httpCode > 0) {
        Serial.printf("[HTTP] POST... code: %d\n", httpCode);
        if (httpCode == 200) {            // status 200
          postDone = 1;
          DynamicJsonDocument docReceived(1024);
          DeserializationError error =  deserializeJson(docReceived, http.getStream());
          if (error) {
            Serial.print("DeserializeJson() failed with code \n");
            Serial.print(error.c_str());
          } else {
            String payloadFromPost = docReceived["topic"].as<String>();
            Serial.print("payloadFromPost: ");
            Serial.println(payloadFromPost);
            const char* fanTopicInside =  docReceived["topic"]["fan"].as<char*>();
            const char* lampTopicInside =  docReceived["topic"]["lamp"].as<char*>();
            const char* breadTopicInside =  docReceived["topic"]["breadType"].as<char*>();
            strncpy(fanTopic,fanTopicInside,sizeof(fanTopic));
            strncpy(lampTopic,lampTopicInside,sizeof(lampTopic));
            strncpy(breadTopic,breadTopicInside,sizeof(breadTopic));
          }           
        }
        if (httpCode == 404) {            // status 404
          Serial.println("ERROR 404");
        }
      } else {
        Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
      }
      http.end();                         // closing the HTTP connection
      Serial.println("Done Connecting");
    }
    return postDone;
  }

  
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//      WIFI CONNECTION
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
void connectWifi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_config.ssid, wifi_config.password);

  Serial.print("Connecting ...");                // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  } 
  Serial.print("connected to wifi with local ip: ");
  Serial.println(WiFi.localIP());
  local_ip = WiFi.localIP().toString();
}

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//     mqtt CONNECTION
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print("Message: "); // {"message":"on"}
  String messageTemp;

  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println("after the for loop");

  Serial.println("using json");
  
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);

  // Test if parsing succeeds.
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  }

  Serial.print("reading the json doc[message]: ");
  const char* messageFromMQTT = doc["message"];
  Serial.println(messageFromMQTT);


  char buf_lamp[17];
  const char *first_lamp = mqtt_config.caseID;
  const char *second_lamp = "/trigger/lamp";
  strcpy(buf_lamp,first_lamp);
  strcat(buf_lamp,second_lamp);

  char buf_fan[17];
  const char *first_fan = mqtt_config.caseID;
  const char *second_fan = "/trigger/fan";
  strcpy(buf_fan,first_fan);
  strcat(buf_fan,second_fan);

  Serial.println("buf_fan and buf_lamp");
  Serial.println(buf_fan);
  Serial.println(buf_lamp);
    
  Serial.println("IN CALLBACK BEFORE COMPARISON");
  if (strcmp(topic, buf_fan) == 0) {
    Serial.print("Changing fan output to ");
    if(strcmp(messageFromMQTT, "on") == 0){
      Serial.println("turning on the fan");
      LightsOn(13);
    }
    else if(strcmp(messageFromMQTT, "off") == 0){
      Serial.println("turning off the fan");
      LightsOff(13);
    }
  }
  if (strcmp(topic, buf_lamp) == 0) {
    Serial.print("Changing lamp output to ");
    if(strcmp(messageFromMQTT, "on") == 0){
      Serial.println("turning lamp on");
      LightsOn(12);
    }
    else if(strcmp(messageFromMQTT, "off") == 0){
      Serial.println("lamp off");
      LightsOff(12);
    }
  }
}
  
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//      MQTT RE-CONNECTION
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(mqtt_config.clientID, mqtt_config.mqtt_username, mqtt_config.mqtt_password)) {
      Serial.println("connected");
      // Once connected, resubscribe to desired topics
      char buf_lamp[17];
      const char *first_lamp = mqtt_config.caseID;
      const char *second_lamp = "/trigger/lamp";
      strcpy(buf_lamp,first_lamp);
      strcat(buf_lamp,second_lamp);

      char buf_fan[17];
      const char *first_fan = mqtt_config.caseID;
      const char *second_fan = "/trigger/fan";
      strcpy(buf_fan,first_fan);
      strcat(buf_fan,second_fan);
      
      client.subscribe(buf_lamp);
      client.subscribe(buf_fan);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000); // retry in 5 seconds
    }
  }
}
