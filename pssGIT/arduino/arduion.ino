int ledPin = 13;  

void setup() {
  pinMode(ledPin, OUTPUT);  
  Serial.begin(9600);  
}

void loop() {
  if (Serial.available() > 0) { 
    char received = Serial.read();  
    if (received == '1') {  
      unsigned long startTime = millis();  
      while (millis() - startTime < 10000) {  
        digitalWrite(ledPin, HIGH);  
        delay(500);  
        digitalWrite(ledPin, LOW);  
        delay(500);  
      }
    } else if (received == '0') {  
      digitalWrite(ledPin, LOW);  
    }
  }
}
