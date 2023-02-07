from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import AWSIoTPythonSDK.exception.AWSIoTExceptions
#import AWSIoTPythonSDK.core.protocol.paho.client 
import logging
import time
import argparse
import json
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)


payload = "SWON"



# Custom MQTT message callback
def customCallback(client, userdata, message):
    payload = json.loads(message.payload)
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

    global payload 

    print (payload)

    if(payload == "ON"):

        GPIO.output(21, True)
        print("Led Encendido")

    elif(payload == "OFF"):

        GPIO.output(21, False)
        print("Led Apagado")

    return payload

def AWSConnect():

    try:
    # Connect to AWS IoT
        myAWSIoTMQTTClient.connect()
        myAWSIoTMQTTClient.subscribe(led, 0, customCallback)
        myAWSIoTMQTTClient.subscribe(switch, 0, customCallback)
        time.sleep(2)
        print("Conexion Establecida con AWS")

    except:
        time.sleep(5)
        print("Conexion Fallida con AWS")
        AWSConnect()

def AWSMessage():

    try:

        myAWSIoTMQTTClient.publish(topic, messageJson, 1)
        myAWSIoTMQTTClient.publish(topicevent, messageJsonevent, 1)

        print('Published topic %s: %s\n' % (topic, messageJson))
        print('Published topic %s: %s\n' % (topicevent, messageJsonevent))

    except AWSIoTPythonSDK.exception.AWSIoTExceptions.publishTimeoutException:

        time.sleep(5)
        print("Reintentando")

def Message(data):

    print(payload)



# Ingresar datos de AWS

host = "a1q9v3uypa506z-ats.iot.us-west-2.amazonaws.com"    #Your AWS IoT custom endpoint
rootCAPath = "/home/pi/CodigosPythonAWSIoT/CertificadosAWSRaspberryPi/rootCA.pem"   #Root CA file path
certificatePath = "/home/pi/CodigosPythonAWSIoT/CertificadosAWSRaspberryPi/certificate.pem.crt"  #Certificate file path
privateKeyPath = "/home/pi/CodigosPythonAWSIoT/CertificadosAWSRaspberryPi/private.pem.key"    #Private key file path
port = 443  #Port number override    (443 or 8883)
useWebsocket = False  #Use MQTT over WebSocket
clientId = "Raspberry"  #Targeted client id
topic = "sdk/test/python"  #Targeted topic
topicevent = "sdk/test/eventos"
led = "sdk/test/led"
switch = "sdk/test/switch"


# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

myAWSIoTMQTTClient.onMessage = Message

#myAWSIoTMQTTClient.loop_start()

# Connect to AWS IoT
# myAWSIoTMQTTClient.connect()
# myAWSIoTMQTTClient.subscribe(led, 0, customCallback)
time.sleep(2)


medicion = {
        'Primer nombre': 'Juan',              #Estos campos son la informacion del documento
        'Segundo nombre': 'Posada',
        'nacimiento': 1997
        }

eventos = {
        'Sobrevoltaje': 280,              #Estos campos son la informacion del documento
        'Sobrecorriente': 100,
        'Sobrepotencia': 1.3
        }

messageJson = json.dumps(medicion)
messageJsonevent = json.dumps(eventos)


AWSConnect()

time.sleep(3)

while True:

    print(payload)
    
    print(type(payload))

    if(payload == "SWON"):

        AWSMessage()

    elif(payload == "SWOFF"):

        print("No se envia mensajes")

    time.sleep(3)