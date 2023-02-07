from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.core.protocol.paho import client as awspaho
import logging
import time
import argparse
import json
import CodigoPWRMeterClick9 as PWRMeter
import threading

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

SelectModeTopic = "PWRMeter/SelectMode"

PublishThresholdsFlag = False
PublishCalibrationFlag = False
RealTimeFlag = False
DebugFlag = False
StoreFlag = False
RealTimeAlertsFlag = False

# Custom MQTT message callback

######################## On_Messages Callbacks#######################

def SelectModeCallback(client, userdata, message):

	global DebugFlag
	global RealTimeFlag
	global StoreFlag
	global RealTimeAlertsFlag
		
	decoded_message = message.payload.decode("utf-8")

	if(decoded_message == "Debug"):         #Se bloquea modo envio de datos y almacenamiento para ejecutar comandos

		DebugFlag = True
		RealTimeFlag = False
		StoreFlag = False

		print("DebugFlag = {}, Realtime = {}, StoreFlag = {}".format(DebugFlag, RealTimeFlag, StoreFlag) )

	elif(decoded_message == "RealTime"):	#Se desactiva el modo debug y se habilita el envio de datos en tiempo real

		DebugFlag = False
		RealTimeFlag = True
		print("DebugFlag = {}, Realtime = {}, StoreFlag = {}".format(DebugFlag, RealTimeFlag, StoreFlag) )

	elif(decoded_message == "Store"):		#Se desactiva el modo debug y se habilita el almacenamiento de datos

		DebugFlag = False
		StoreFlag = True
		print("DebugFlag = {}, Realtime = {}, StoreFlag = {}".format(DebugFlag, RealTimeFlag, StoreFlag) )

	elif(decoded_message == "RealStore"):	#Se desactiva el modo debug y se habilitan el envio de datos en tiempo real y almacenamiento

		DebugFlag = False
		RealTimeFlag = True
		StoreFlag = True
		print("DebugFlag = {}, Realtime = {}, StoreFlag = {}".format(DebugFlag, RealTimeFlag, StoreFlag) )

	elif(decoded_message == "SetRealAlerts"):

		RealTimeAlertsFlag = True

	elif(decoded_message == "NoRealAlerts"):

		RealTimeAlertsFlag = False	

def SetThresholdsValuesCallback(client, userdata, message):
    
	if(DebugFlag == True):

		m_out = json.loads(message.payload)
		PWRMeter.SetEventsLimits( m_out['VSagLimit'] , m_out['VSurgeLimit'], m_out['OverCurrent'], m_out['OverPower'])
		upload = PWRMeter.ReadEventsLimits()	  
		print(upload)
		print("Se ha ejecutado Comando de ajuste de umbrales") 

def SetCalibrationValuesCallback(client, userdata, message):
    
    if(DebugFlag == True):

    	m_out = json.loads(message.payload)
    	PWRMeter.SetCalibrationValues( m_out['VoltageCal'] , m_out['CurrentCal'] , m_out['PowerActCal'])
    	upload = PWRMeter.ReadCalibrationValues()
    	print (upload)
    	print ("Se ha ejecutado Comando de ajuste valores Calibracion")

def FixedCommandsCallBack(client, userdata, message):

	global DebugFlag

	decoded_message = message.payload.decode("utf-8")

	if(DebugFlag == True and decoded_message == "SaveFlash"):

		PWRMeter.SaveToFlash()

	elif(DebugFlag == True and decoded_message == "SaveEnergyCounters"):

		PWRMeter.SaveEnergyCounters()

	elif(DebugFlag == True and decoded_message == "AutoCalibrationGain"):

		PWRMeter.AutoCalibrationGain()

	elif(DebugFlag == True and decoded_message == "AutoCalibrationFrequency"):

		PWRMeter.AutoCalibrationFrequency()


################### Thread Functions #####################################

def RealTimeValues():

	global RealTimeFlag
	print("Ejecutando hilo RealTime")
	while(True):

		if(RealTimeFlag == True):

			RealTime = PWRMeter.GetValues()
			myAWSIoTMQTTClient.publish(RealSendLoopTopic, json.dumps(RealTime), qos=1)
			time.sleep(5)

def RealTimeAlerts():

	global RealTimeAlertsFlag	
	print("Ejecutando Hilo de Alertas")	

	while(True):

		if(RealTimeAlertsFlag == True):

			RealTimeAlerts = PWRMeter.ScanEvents()
			myAWSIoTMQTTClient.publish(EventTopic, json.dumps(RealTimeAlerts), qos=1)
			time.sleep(5)
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
myAWSIoTMQTTClient.connect(keepAliveIntervalSecond=300)
#myAWSIoTMQTTClient.subscribe(EventTopic, 1, customCallback)

# myAWSIoTMQTTClient.subscribe(RealSendLoopTopic, 1, LoopCallBack)
# myAWSIoTMQTTClient.subscribe(FixedCommandsTopic, 1, FixedCommandsCallBack)
# myAWSIoTMQTTClient.subscribe(ThresholdsTopic, 1, SetThresholdsValuesCallback)
# myAWSIoTMQTTClient.subscribe(CalibrationTopic, 1, SetCalibrationValuesCallback)

myAWSIoTMQTTClient.subscribe(FixedCommandsTopic, 1, FixedCommandsCallBack)
myAWSIoTMQTTClient.subscribe(ThresholdsTopic, 1 , SetThresholdsValuesCallback)
myAWSIoTMQTTClient.subscribe(CalibrationTopic , 1 , SetThresholdsValuesCallback)
myAWSIoTMQTTClient.subscribe(SelectModeTopic, 1 , SelectModeCallback)

#PWRMeter.LatchEvents()
#PWRMeter.SetEventsLimits(330, 1000, 500000, 410000) 
hilo1 = threading.Thread(target=RealTimeValues)
hilo2 = threading.Thread(target=RealTimeAlerts)

hilo1.start()
hilo2.start()

time.sleep(2)

try:
	while True:
	
		# Values = PWRMeter.GetValues() 
		# ValuesJson = json.dumps(Values)
		# mqttc.publish(MeasurementTopic , ValuesJson , qos=1)
		# print('Published topic %s: %s\n' % (MeasurementTopic, ValuesJson))

		# time.sleep(0.5)

		# EnergyAccum = PWRMeter.EnergyAccumValues()
		# EnergyAccumJson = json.dumps(EnergyAccum)
		# mqttc.publish(EnergyTopic , EnergyAccumJson, qos=1)
		# print('Published topic %s: %s\n' % (EnergyTopic, EnergyAccumJson))

		# time.sleep(0.5)

		# EventsFlag = PWRMeter.ScanEvents() 	    
		# EventsJson = json.dumps(EventsFlag)
		# mqttc.publish(EventTopic, EventsJson, qos=1)
		# print('Published topic %s: %s\n' % (EventTopic, EventsJson))

		# time.sleep(0.5)
		if(StoreFlag == True and DebugFlag == False):

			print("Almacenamiento de datos activado")

			Values = PWRMeter.GetValues() 
			EnergyAccum = PWRMeter.EnergyAccumValues()
			EventsFlag = PWRMeter.ScanEvents() 	    
		
			EventsJson = json.dumps(EventsFlag)
			EnergyAccumJson = json.dumps(EnergyAccum)
			ValuesJson = json.dumps(Values)

			myAWSIoTMQTTClient.publish(MeasurementTopic , ValuesJson ,1)
			myAWSIoTMQTTClient.publish(EnergyTopic , EnergyAccumJson, 1)
			myAWSIoTMQTTClient.publish(EventTopic, EventsJson, 1)

			print('Published topic %s: %s\n' % (MeasurementTopic, ValuesJson))
			print('Published topic %s: %s\n' % (EnergyTopic, EnergyAccumJson))
			print('Published topic %s: %s\n' % (EventTopic, EventsJson))

			time.sleep(600)

	# Disconnect from MQTT_Broker
	#mqttc.disconnect()

except KeyboardInterrupt:

	print("Programa Finalizado por Usuario ")