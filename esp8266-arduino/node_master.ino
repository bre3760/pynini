#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <ESP8266HTTPClient.h>

// function prototypes

boolean connectWifi();
void httpConnect();
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
const char* mqtt_server = "192.168.1.11"; // the raspberry ip

// Creation of an ESP8266WiFi object
WiFiClient espClient;
// Creation of a PubSubClient object
PubSubClient client(espClient);


void setup() {
  Serial.begin(9600);
  // Initialise wifi connection
  wifiConnected = connectWifi();
  local_ip = WiFi.localIP().toString();

  // send post request to catalog
  httpConnect();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  Wire.begin(D1, D2); // join i2c bus with SDA=D1 and SCL=D2 of NodeMCU

}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.print("void loop starting \n");

  if (!client.connected()) {
    reconnect();
  }
  client.loop();


  breadType = Wire.requestFrom(8,1);
  Serial.print("The Bread type from button is: ");
  Serial.print(breadType);
  Serial.print("\n");
  client.publish("breadType/","{\"msg\": breadType}");
  delay(200);






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


void httpConnect()
  {
    HTTPClient http;
    // opening the connection with the URL of the room catalog
    http.begin("http://192.168.1.88:9090/addSensor");
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");

    String httpRequestData = "dev_name=arduino&ip="+local_ip+"name=esp-arduino";
    // code response of the POST request
    int httpCode = http.POST(httpRequestData);

    Serial.print("HTTP response code: ");
    Serial.print(httpCode);
    Serial.print("\n");
    http.end(); // closing the HTTP connection
  }


boolean connectWifi(){
  boolean state = true;
  int i = 0;

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.println("");
  Serial.println("Connecting to WiFi");

  // Wait for connection
  Serial.print("Connecting ...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (i > 10){
      state = false;
      break;
    }
    i++;
  }

  if (state){
    Serial.println("");
    Serial.print("Connected to ");
    Serial.println(ssid);
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  }
  else {
    Serial.println("");
    Serial.println("Connection failed.");
  }

  return state;
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
}


void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += "LightsRelay";

    // Attempt to connect
    if (client.connect(clientId.c_str())) {
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