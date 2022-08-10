import RPi.GPIO as GPIO
import time
def light_ON(pin):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin,GPIO.OUT)
    GPIO.output(pin,GPIO.HIGH)
def light_OFF(pin):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin,GPIO.OUT)
    GPIO.output(pin,GPIO.LOW)
if __name__=='__main__':
    light_OFF(21)
    light_OFF(4)
    light_OFF(18)
    time.sleep(5)
    light_ON(21)
    light_ON(4)
    light_ON(18)

