/*
 * Sonar Mapper — pool calibration firmware
 * Extracted from the TIPE report, Annexe 4 (comments and variable names
 * translated to English, logic unchanged).
 *
 * Logs the raw round-trip echo duration (in microseconds and seconds) to
 * the SD card. Used to measure the speed of sound over a known distance
 * in fresh/salt water at controlled temperature (see README > Results).
 */

#include <SD.h>
#include <SPI.h>

const int trigPin = 9;
const int echoPin = 10;
const int chipSelect = 4;

File logFile;

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  SD.begin(chipSelect);

  logFile = SD.open("time.txt", FILE_WRITE); // create/open "time.txt"
  logFile.println("Measured durations (in microseconds and seconds):");
  logFile.close();
}

void loop() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 1000000UL);
  float duration_sec = duration / 1e6;

  logFile = SD.open("time.txt", FILE_WRITE);
  logFile.print("Duration: ");
  logFile.print(duration);
  logFile.print(" microseconds (");
  logFile.print(duration_sec, 6);
  logFile.println(" seconds)");
  logFile.close();

  delay(1000);
}
