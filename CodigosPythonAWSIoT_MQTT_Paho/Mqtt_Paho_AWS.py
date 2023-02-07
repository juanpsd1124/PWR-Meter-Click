# Import package
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import ssl
import time
import sys
import datetime
import json
import threading
import CodigoPWRMeterClick9 as PWRMeter

#################### Flags ########################################

PublishThresholdsFlag = False
PublishCalibrationFlag = False
RealTimeFlag = False
DebugFlag = False
StoreFlag = False
RealTimeAlertsFlag = False

#################### Credentials to Access#########################

MQTT_HOST = "a1q9v3uypa506z-ats.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "C:/CertificadosAWSRaspberryPi/AmazonRootCA1.pem"
THING_CERT_FILE = "C:/CertificadosAWSRaspberryPi/certificate.pem.crt"
THING_PRIVATE_KEY = "C:/CertificadosAWSRaspberryPi/private.pem.key"
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 528
clientId = "Raspberry"  #Targeted client id

################### Topics #########################################

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

def on_log(client, userdata, level, buf):
    print("log: ",buf)

# Define on_publish event function
def on_publish(client, userdata, mid):
	print ("Message Published at¨:" , datetime.datetime.now())


def on_subscribe(client, userdata, mid, granted_qos):

	print("Suscrito a tema correctamente")
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

def RealTimeValues():  #Se activa enviando mensaje RealTime

	global RealTimeFlag
	print("Ejecutando hilo RealTime")
	while(True):

		if(RealTimeFlag == True):

			RealTime = PWRMeter.GetValues()
			mqttc.publish(RealSendLoopTopic, json.dumps(RealTime), qos=1)

		time.sleep(5)	

def RealTimeAlerts():

	global RealTimeAlertsFlag	
	print("Ejecutando Hilo de Alertas")	

	while(True):

		if(RealTimeAlertsFlag == True):

			RealTimeAlerts = PWRMeter.ScanEvents()
			mqttc.publish(EventTopic, json.dumps(RealTimeAlerts), qos=1)
			
		time.sleep(5)

# Initiate MQTT Client
mqttc = mqtt.Client()

# Register publish callback function
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_log = on_log

# Configure TLS Set
mqttc.tls_set(ca_certs=CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

######################## Subscribe to Topics######################


mqttc.subscribe([ (FixedCommandsTopic,1),
				  (ThresholdsTopic,1),
				  (CalibrationTopic,1),
				  (RealSendLoopTopic,1),
				  (SelectModeTopic,1)
				])

mqttc.message_callback_add(FixedCommandsTopic, FixedCommandsCallBack)
mqttc.message_callback_add(ThresholdsTopic, SetThresholdsValuesCallback)
mqttc.message_callback_add(CalibrationTopic, SetCalibrationValuesCallback)
mqttc.message_callback_add(SelectModeTopic, SelectModeCallback)

mqttc.loop_start()

hilo1 = threading.Thread(target=RealTimeValues)
hilo2 = threading.Thread(target=RealTimeAlerts)

hilo1.start()
hilo2.start()

numthreads = threading.active_count()

print("El numero de hilos activos es: " ,numthreads)

for thread in threading.enumerate():

	print(thread.name)


try:
	while True:    # Se activa al enviar Store

		if(StoreFlag == True and DebugFlag == False):

			print("Almacenamiento de datos activado")

			Values = PWRMeter.GetValues() 
			EnergyAccum = PWRMeter.EnergyAccumValues()
			EventsFlag = PWRMeter.ScanEvents() 	    
		
			EventsJson = json.dumps(EventsFlag)
			EnergyAccumJson = json.dumps(EnergyAccum)
			ValuesJson = json.dumps(Values)

			mqttc.publish(MeasurementTopic , ValuesJson , qos=1)
			mqttc.publish(EnergyTopic , EnergyAccumJson, qos=1)
			mqttc.publish(EventTopic, EventsJson, qos=1)

			print('Published topic %s: %s\n' % (MeasurementTopic, ValuesJson))
			print('Published topic %s: %s\n' % (EnergyTopic, EnergyAccumJson))
			print('Published topic %s: %s\n' % (EventTopic, EventsJson))

		time.sleep(20)
	
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


			

		

	# Disconnect from MQTT_Broker
	#mqttc.disconnect()

except KeyboardInterrupt:

	print("Programa Finalizado por Usuario ")