# Import package
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import ssl
import time
import sys
import datetime
import json
import threading
import CodigoPWRMeterClick13 as PWRMeter
import schedule
import statistics as stats

hora = datetime.datetime.now()

#################### Flags ########################################

PublishThresholdsFlag = False
PublishCalibrationFlag = False
RealTimeFlag = False
DebugFlag = False
StoreFlag = True
RealTimeAlertsFlag = True

#################### Credentials to Access#########################

MQTT_HOST = "a1q9v3uypa506z-ats.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "C:/CertificadosAWSRaspberryPi/AmazonRootCA1.pem"
THING_CERT_FILE = "C:/CertificadosAWSRaspberryPi/certificate.pem.crt"
THING_PRIVATE_KEY = "C:/CertificadosAWSRaspberryPi/private.pem.key"
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 300
clientId = "Raspberry"  #Targeted client id


################### Topics #########################################

StoreTopic = 	   "PWRMeter/Store"                       		#Topico para publicar Valores en AWS IoT
AlertTopic =       "PWRMeter/Alerts"                       		#Topico para publicar Alertas en AWS IoT
CalibrationTopic = "PWRMeter/Calibration"                       #Topico para ejecutar Comandos de Calibracion (Desde App)
ThresholdsTopic =  "PWRMeter/Thresholds"                        #Topico para ejecutar Comandos de Umbrales (Desde App)
FixedCommandsTopic = "PWRMeter/FixedCommands"                   #Topico para ejecurar Fixed Commands

CalibrationValuesTopic = "PWRMeter/Calibration/Values"          #Topico para enviar Valores de Calibracion y Confirmacion de comando hacia AWS IoT
ThresholdsValuesTopic =  "PWRMeter/Thresholds/Values"           #Topico para enviar Valores de Umbrales y Confirmacion de comando hacia AWS IoT

RealSendLoopTopic = "PWRMeter/RealTime"

SelectModeTopic = "PWRMeter/SelectMode" ##Topico para seleccionar modo

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

		RealTimeFlag = False
		StoreFlag = False
		DebugFlag = True

		print("DebugFlag = {}, Realtime = {}, StoreFlag = {}".format(DebugFlag, RealTimeFlag, StoreFlag) )

	elif(decoded_message == "RealTime"):	#Se desactiva el modo debug y se habilita el envio de datos en tiempo real

		DebugFlag = False
		StoreFlag = False
		RealTimeFlag = True

		print("DebugFlag = {}, Realtime = {}, StoreFlag = {}".format(DebugFlag, RealTimeFlag, StoreFlag) )

	elif(decoded_message == "Store"):		#Se desactiva el modo debug y se habilita el almacenamiento de datos

		DebugFlag = False
		RealTimeFlag = False
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

			RealTime, ActPWRAccum, ReactPWRAccum = PWRMeter.GetValues()
			ValuesDict = { 'voltaje':  RealTime[0] ,
                           'corriente' : RealTime[1]  ,
                           'potencia activa'  : RealTime[2], 
                           'potencia reactiva' :RealTime[3],
                           'potencia aparente' :RealTime[4]  , 
                           'frecuencia' : RealTime[5]  ,
                           'temperatura' : RealTime[6] ,
                           'potencia activa consumida' : ActPWRAccum,
                           'potencia consumida reactiva' : ReactPWRAccum}

			mqttc.publish(RealSendLoopTopic, json.dumps(ValuesDict), qos=1)

		time.sleep(5)	

def RealTimeAlerts():

	global RealTimeAlertsFlag
	global AlertsDict
	#print("Ejecutando Hilo de Alertas")	

	AlertsDict = {'VSag':  False, 
			  	  'VSurge' : False, 
			 	  'OverCurrent' : False, 
			  	  'OverPower' : False, 
			  	  'NoEvent': True, 
			  	  'hora' : hora.strftime("%x") 
			  	 }

	#while(True):

		#if(RealTimeAlertsFlag == True):

	RealAlerts = PWRMeter.ScanEvents()

	AlertsDict = {'VSag':  RealAlerts[0], 
				  'VSurge' : RealAlerts[1], 
				  'OverCurrent' : RealAlerts[2], 
				  'OverPower' : RealAlerts[3], 
				  'NoEvent': RealAlerts[4], 
				  'hora' : hora.strftime("%x") }

	if(PWRMeter.AlertByte != 0x0):

		#print(AlertsDict)

		mqttc.publish(AlertTopic, json.dumps(AlertsDict), qos=1)

		PWRMeter.ClearEvents()
		
	#time.sleep(3)

############################### Schedule Functions ##############################################################################

def UploadDatabaseValues():

	global hora

	if(StoreFlag == True):

		PromValues = {
						'voltajeprom': round (stats.mean( PWRMeter.ValuesSum[0] ) , 2)      ,
						'corrienteprom': round ( stats.mean( PWRMeter.ValuesSum[1] ), 2)    ,
						'potencia_act_prom': round( stats.mean( PWRMeter.ValuesSum[2] ) , 2)  ,
						'potenciareact_prom': round( stats.mean( PWRMeter.ValuesSum[3] ), 2) ,
						'potencia_app_prom': round ( stats.mean( PWRMeter.ValuesSum[4] ), 2)  ,
						'frecuenciaprom': round ( stats.mean( PWRMeter.ValuesSum[5] ),  2)  ,
						'temperaturaprom': round( stats.mean( PWRMeter.ValuesSum[6] ),  2)  ,
						'potencia_accum_prom': PWRMeter.ValuesSum[7],
						'id_fechahora': hora.strftime("%x %X"),						
						'fecha' : hora.strftime("%x"),
						'hora' : hora.strftime("%X")  
						#'potencia_accum_react': PWRMeter.ValuesSum[8]
					 }

		print(PromValues)

		mqttc.publish(StoreTopic, json.dumps(PromValues), qos=1)


		for i in range(0,7):

			PWRMeter.ValuesSum[i].clear()

		print("Datos enviados a Base de datos a las: " , datetime.datetime.now())		

# MQTT init and Connect
mqttc = mqtt.Client()
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_log = on_log
mqttc.tls_set(ca_certs=CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
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

##################### Set Schedule Jobs ###################################################################

schedule.every(0.1).minutes.do(UploadDatabaseValues)


################################ Thread Functions Init#####################################################

hilo1 = threading.Thread(target=RealTimeValues)
#hilo2 = threading.Thread(target=RealTimeAlerts)

hilo1.start()
#hilo2.start()

PWRMeter.LatchEvents()

################################ 

try:

	while(True):

		schedule.run_pending()

		if(StoreFlag == True):

			PWRMeter.SumValues() 

		time.sleep(0.3)

		if(RealTimeAlertsFlag == True):

			RealTimeAlerts()

		time.sleep(0.3)


		
except KeyboardInterrupt:

	print("Programa Finalizado por Usuario ")


