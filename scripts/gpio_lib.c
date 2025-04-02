#include <wiringPi.h>
#include <stdio.h>

#define LED 0 // PIN for LED. This is GPIO 0 

void setupIO(void){
	printf("Setting up IO\n");
	wiringPiSetup(); 
	pinMode(LED,OUTPUT);
}

//Trigger heartbeat
void beat(void){
	digitalWrite(LED, HIGH);
	delay(100);
	digitalWrite(LED,LOW);
}
