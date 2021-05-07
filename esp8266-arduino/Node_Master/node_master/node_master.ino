#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <string.h>
#include <typeinfo>
// function prototypes

void connectWifi();
int httpConnect(char*, char*, char*);
void LightsOn(int actuatorPin);
void LightsOff(int actuatorPin);
void callback(char* topic, byte* message, unsigned int length);

// variables and constants

const char* ssid="McLovin";
const char* password = "sCkjiSFb25p9rmKL";
boolean wifiConnected = false;
String local_ip;

const int relayPin1 = 5;    //I am using ESP8266 EPS-12F GPIO5 and GPIO4
const int relayPin2 = 4;
int breadType;

// mqtt 
const char* mqtt_server = "192.168.1.2"; // the raspberry ip
const char* mqtt_username ="brendan";
const char* mqtt_password = "pynini";
const char* clientID = "esp-arduino";
const char* topic = "breadType/";

char breadTopic[10];
char fanTopic[11];
char lampTopic[12];
String breadTopicString;
String fanTopicString;
String lampTopicString;
// http

String rpi_ip = "192.168.1.2"; // the raspberry ip for http request
String rpi_port ="9090";

// Creation of an ESP8266WiFi object
WiFiClient espClient;
// Creation of a PubSubClient object
PubSubClient client(mqtt_server,1883,espClient);

void setup() {
  Serial.begin(115200);
  connectWifi();                           // Initialise wifi connection

  int got_topics = 0;
  got_topics = httpConnect(breadTopic,fanTopic,lampTopic);           // send post request to catalog 
  delay(7000);
  Serial.println("got_topics value: ");
  Serial.println(got_topics);
  
  
  client.setCallback(callback);            // create callback function for mqtt
  
  Wire.begin(D1, D2);                      // join i2c bus with SDA=D1 and SCL=D2 of NodeMCU 
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
    Serial.print("This is c: ");
    Serial.print(c);
    Serial.print("\n");
    breadData += c;
  }

    Serial.print("The Bread type from button is: ");
    Serial.print(breadData);
    Serial.print("\n");

  String messageDescription = "message" ;
  String payload = "{";
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

  
  if( client.publish(breadTopic, payload.c_str()) ){
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
    Serial.print("Switch 2 turn on ...");
      Wire.beginTransmission(8); /* begin with device address 8 */
      Wire.write("{\"gpio\":actuatorPin,\"state\":1}");  
      Wire.endTransmission();    /* stop transmitting */
}

void LightsOff(int actuatorPin) {
  Serial.print("Switch 2 turn off ...");
    Wire.beginTransmission(8); /* begin with device address 8 */
    Wire.write("{\"gpio\":actuatorPin,\"state\":0}");  
    Wire.endTransmission();    /* stop transmitting */
}

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//      HTTP CONNECTION
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

int httpConnect(char*, char*, char*)
  {
    int postDone=0;
    if ((WiFi.status() == WL_CONNECTED)) {
      HTTPClient http; 
      DynamicJsonDocument doc(1024);    
      doc["name"] = "arduino";
      doc["ip"] = local_ip;
      doc["port"] = "8080";
      doc["last_seen"] = "01:00";
      doc["dev_name"] = "arduino";
      doc["caseID"] = "CCC1";
      doc["sensorID"] = "arduino";
      String jsonData;
      serializeJson(doc,jsonData);
      int httpCode;
      String urlForPost = "http://" + rpi_ip + ":"+rpi_port + "/addSensor";
      http.useHTTP10(true);
      http.begin(espClient,urlForPost); 
      http.addHeader("Content-Type", "application/json");
      httpCode = http.POST(jsonData);        // code response of the POST request
      Serial.print("HTTP response code: ");
      Serial.println(httpCode);

      if (httpCode > 0) {
        Serial.printf("[HTTP] POST... code: %d\n", httpCode);
        if (httpCode == 200) { // status 200
          postDone = 1;
          DynamicJsonDocument docReceived(1024);
          DeserializationError error =  deserializeJson(docReceived, http.getStream());
          if (error) {
            Serial.print("DeserializeJson() failed with code \n");
            Serial.print(error.c_str());
          } else {
            String payloadFromPost = docReceived["topic"].as<String>();
            Serial.println(payloadFromPost);
            const char* fanTopicInside =  docReceived["topic"]["fan"].as<char*>();
            const char* lampTopicInside =  docReceived["topic"]["lamp"].as<char*>();
            const char* breadTopicInside =  docReceived["topic"]["breadType"].as<char*>();
            strncpy(fanTopic,fanTopicInside,sizeof(fanTopic));
            strncpy(lampTopic,lampTopicInside,sizeof(lampTopic));
            strncpy(breadTopic,breadTopicInside,sizeof(breadTopic));

    
          }           
//          const String& payload = http.getString();
//          Serial.println("received payload:\n<<");
//          Serial.println(payload);
//          Serial.println(">>");
            
        }
        if (httpCode == 404) { // status 404
          Serial.println("ERROR 404");
        }
        } else {
          Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
      }
    
      http.end(); // closing the HTTP connection
      
      Serial.println("Done Connecting");
    }
    return postDone;
  }

  
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//      WIFI CONNECTION
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
void connectWifi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting ...");                // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  } 
  Serial.print("connected to wifi with local ip: ");
  Serial.println(WiFi.localIP());
  local_ip = WiFi.localIP().toString();
}


void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println();

  if (String(topic) == "trigger/fan") {
    Serial.print("Changing fan output to ");
    if(messageTemp == "on"){
      Serial.println("on");
      LightsOn(13);
    }
    else if(messageTemp == "off"){
      Serial.println("off");
      LightsOff(13);
    }
  }
  if (String(topic) == "trigger/lamp") {
    Serial.print("Changing fan output to ");
    if(messageTemp == "on"){
      Serial.println("lamp on");
      LightsOn(12);
    }
    else if(messageTemp == "off"){
      Serial.println("lamp off");
      LightsOff(12);
    }
  }
}


void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(clientID, mqtt_username,mqtt_password)) {
      Serial.println("connected");
      // Once connected, resubscribe to desired topics
      client.subscribe("trigger/light");
      client.subscribe("trigger/fan");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000); // retry in 5 seconds
    }
  }
}