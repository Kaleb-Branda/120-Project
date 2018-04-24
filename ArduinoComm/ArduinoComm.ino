void setup() {
  // Sample at a rate of 9600 Samples/Sec (9.6 kHz)
  Serial.begin(9600);
}
 
void loop() {
  // Get Sensor Values from the respective Sensors
  int right = analogRead(A0);
  int left = analogRead(A1);
  // Convert to sendable packets
  sendToPC(&right);
  sendToPC(&left);

}
 
void sendToPC(int* data)
{
  byte* byteData = (byte*)(data);
  // Send to the Serial Port to communicate with Python
  Serial.write(byteData, 2);
}
