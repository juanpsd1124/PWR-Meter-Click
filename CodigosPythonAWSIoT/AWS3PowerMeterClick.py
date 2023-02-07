from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.core.protocol.paho import client as awspaho
import logging
import time
import argparse
import json
import CodigoPWRMeterClick9 as PWRMeter
import threading
import schedule

AllowedActions = ['both', 'publish', 'subscribe']


######################################## Topics ######################################################################

MeasurementTopic = "PWRMeter/Measurement"                       #Topico para publicar Valores en AWS IoT
EnergyTopic =      "PWRMeter/Measurement/EnergyMeters"          #Topico para publicar Valores Energia Acumulada en AWS IoT
EventTopic =            "PWRMeter/Events"                       #Topico para publicar Alertas en AWS IoT
CalibrationTopic = "PWRMeter/Calibration"                       #Topico para ejecutar Comandos de Calibracion (Desde App)
ThresholdsTopic = "PWRMeter/Thresholds"                         #Topico para ejecutar Comandos de Umbrales (Desde App)
FixedCommandsTopic = "PWRMeter/FixedCommands"                   #Topico para ejecurar Fixed Commands

CalibrationValuesTopic = "PWRMeter/Calibration/Values"          #Topico para enviar Valores de Calibracion y Confirmacion de comando hacia AWS IoT
ThresholdsValuesTopic =  "PWRMeter/Thresholds/Values"           #Topico para enviar Valores de Umbrales y Confirmacion de comando hacia AWS IoT

RealSendLoopTopic = "PWRMeter/SendLoop"

led = "sdk/test/led"


PublishThresholdsFlag = False
PublishCalibrationFlag = False
RealtimeFlag = False

# Custom MQTT message callback

def LoopCallBack(client, userdata, message):

	global RealtimeFlag

	decoded_message = decoded_message = message.payload.decode("utf-8")

	if(decoded_message == "Start"):

		RealtimeFlag = True

	elif(decoded_message == "Stop"):

		RealtimeFlag = False


def SetThresholdsValuesCallback(client, userdata, message):

	global PublishThresholdsFlag

	print("Received a new message:")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")
	print(type(message.topic))

	m_out = json.loads(message.payload)

	PWRMeter.SetEventsLimits( m_out['VSagLimit'] , m_out['VSurgeLimit'], m_out['OverCurrent'], m_out['OverPower'])

	PublishThresholdsFlag = True
    

def SetCalibrationValuesCallback(client, userdata, message):

	global PublishCalibrationFlag

	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")
	print(type(message.topic))

	m_out = json.loads(message.payload)

	PWRMeter.SetCalibrationValues( m_out['VoltageCal'] , m_out['CurrentCal'] , m_out['PowerActCal'])

	PublishCalibrationFlag = True

	#myAWSIoTMQTTClient.publish(CalibrationValuesTopic, json.dumps(upload), 1)


def FixedCommandsCallBack(client, userdata, message):

    decoded_message = message.payload.decode("utf-8")

    if(decoded_message == "SaveFlash"):

        PWRMeter.SaveToFlash()

    elif(decoded_message == "SaveEnergyCounters"):

        PWRMeter.SaveEnergyCounters()

    elif(decoded_message == "AutoCalibrationGain"):

        PWRMeter.AutoCalibrationGain()

    elif(decoded_message == "AutoCalibrationFrequency"):

        PWRMeter.AutoCalibrationFrequency()

# Read in command-line parameters

host = "a1q9v3uypa506z-ats.iot.us-west-2.amazonaws.com"
rootCAPath = "C:/CertificadosAWSRaspberryPi/rootCA.pem"   #Root CA file path
certificatePath = "C:/CertificadosAWSRaspberryPi/certificate.pem.crt"  #Certificate file path
privateKeyPath = "C:/CertificadosAWSRaspberryPi/private.pem.key"    #Private key file path
port = 443  #Port number override    (443 or 8883)
useWebsocket = False  #Use MQTT over WebSocket
clientId = "Raspberry"  #Targeted client id
  #Targeted topic



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

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
#myAWSIoTMQTTClient.subscribe(EventTopic, 1, customCallback)

myAWSIoTMQTTClient.subscribe(RealSendLoopTopic, 1, LoopCallBack)
myAWSIoTMQTTClient.subscribe(FixedCommandsTopic, 1, FixedCommandsCallBack)
myAWSIoTMQTTClient.subscribe(ThresholdsTopic, 1, SetThresholdsValuesCallback)
myAWSIoTMQTTClient.subscribe(CalibrationTopic, 1, SetCalibrationValuesCallback)


#PWRMeter.LatchEvents()
#PWRMeter.SetEventsLimits(330, 1000, 500000, 410000) 

time.sleep(2)

while(True):

