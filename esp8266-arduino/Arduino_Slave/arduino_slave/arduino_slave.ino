#include <Wire.h>
#include <ArduinoJson.h>

int inputPin = 11;
int reading;
int previous=LOW;
long time_passed = 0;
long debounce=200;

int numberOfBreads = 3;
int chooseBread [3] = {10,9,8};
int choiches [3] = {0,1,2};
int timesPressed = 0;
int outPinIndex=0;
int outPin;

void setup() {
 Serial.begin(9600);           /* start serial for debug */
 Wire.begin(8);                /* join i2c bus with address 8 */
 Wire.onReceive(receiveEvent); /* register receive event */
 Wire.onRequest(requestEvent);
  
 pinMode(13, OUTPUT); // fan actuator
 pinMode(12, OUTPUT); // lamp actuator
 pinMode(11, INPUT);  // for the button input
 pinMode(10, OUTPUT); // controlled by the button
 pinMode(9, OUTPUT);  // controlled by the button
 pinMode(8, OUTPUT);  // controlled by the button

 digitalWrite(13, LOW);
 int testing13 = digitalRead(13);
 Serial.print(testing13);
 
}

void loop() {

  reading = digitalRead(inputPin);
  
  // if the input just went from LOW and HIGH and we've waited long enough
  // to ignore any noise on the circuit, toggle the output pin and remember
  // the time
  if (reading == HIGH && previous == LOW && millis() - time_passed > debounce) {
 
    outPinIndex = timesPressed % 3; // find which led to turn on
    outPin = chooseBread[outPinIndex]; // this is the pin for the led to turn on
    Serial.print("which led should be on: ");
    Serial.print(outPin);
    Serial.print("\n");

    // i also need to turn off the others
    for (int i=0; i<numberOfBreads; i++){
      if (i == outPinIndex){
              digitalWrite(outPin, HIGH);
        } else {
              digitalWrite(chooseBread[i], LOW);
        }
    }
    timesPressed++;
    time_passed = millis();
  }
  previous = reading;
}

void processCall(String command){
  
      DynamicJsonDocument doc(1024);
      DeserializationError error =  deserializeJson(doc, command);
       if (error) {
        Serial.print("DeserializeJson() failed with code \n");
        Serial.print(error.c_str());
        }
       else {
          
          char gpio = (doc["gpio"]);
          Serial.print("the gpio chosen is: \n");
          Serial.println(gpio);
          char state = (doc["state"]);
          Serial.print("The state to set is: \n");
          Serial.println(state);
          char level;
          int pin = int(gpio);
          //set GPIO state  
          if (state == 1){
            level = HIGH;
            Serial.print("The level is: \n");
            Serial.println(level);
          }
          else{
            level = LOW;
          }
          digitalWrite(gpio, level);
       }
}


// function that executes when data is received from master
void receiveEvent(int howMany) {
  String data="";
 while (0 < Wire.available()) {
    char c = Wire.read();      /* receive byte as a character */
    data += c;
  }
    Serial.print("the data received is: \n");
    Serial.println(data);           /* print the request data */
    Serial.print("end of data\n");
    processCall(data);         /* to newline */
}


void requestEvent(){
  Serial.println("value before casting is: ");
  Serial.print(outPinIndex);
  Serial.print("\n");
  
  String val = String(outPinIndex);
  Serial.println("value after casting is: ");
  Serial.print(val.c_str());
  Serial.print("\n");
  Wire.write(val.c_str());
  //Wire.write("{\"bread_chosen\":outPinIndex}")
  //Wire.write(String(outPinIndex)); // corresponds to the type of bread chosen 0,1,2
}
