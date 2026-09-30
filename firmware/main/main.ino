/*
 * Sonar Mapper — main acquisition firmware
 * Extracted from the TIPE report, Annexes 1-2 (comments translated to English,
 * logic unchanged).
 *
 * Pipeline: trigger an ultrasonic ping -> measure echo travel time ->
 * read the GPS fix -> log lat,lon,distance to the SD card.
 *
 * NOTE (see README > Design Notes): the distance below is computed using
 * the speed of sound in AIR (0.034 cm/us). This is the firmware used for
 * the in-air validation test. For underwater use, this line should log
 * the raw `duration` instead of a pre-computed distance, so the SVP
 * correction (processing/svp_correction.py) can be applied afterward
 * with the actual local speed of sound. See README > Roadmap.
 */

#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include <SPI.h>
#include <SD.h>

// Pin assignment
const int trigPin = 9;
const int echoPin = 10;
const int chipSelect = 8;

// GPS
SoftwareSerial gpsSerial(4, 3); // RX, TX
TinyGPSPlus gps;

File dataFile;

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // SD card initialization
  if (!SD.begin(chipSelect)) {
    Serial.println("SD card error!");
    while (1); // halt
  }
  Serial.println("SD card OK!"); // init test
} // end of setup

void loop() { // main loop
  // GPS read
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read()); // GPS test
  }

  // Distance measurement
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2; // in air, cm

  // GPS data
  float latitude = gps.location.isValid() ? gps.location.lat() : 0.0;
  float longitude = gps.location.isValid() ? gps.location.lng() : 0.0;

  // Create/open "coordinates.txt"
  dataFile = SD.open("coordinates.txt", FILE_WRITE);

  if (dataFile) {
    // write latitude,longitude,distance
    dataFile.print(latitude, 6);
    dataFile.print(",");
    dataFile.print(longitude, 6);
    dataFile.print(",");
    dataFile.println(distance);
    dataFile.close();
    Serial.println("Data logged"); // close test
  } else {
    Serial.println("File open error"); // write test
  }

  delay(1000); // 1-second delay
}
