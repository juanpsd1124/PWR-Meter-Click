# Import package
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

import ssl
import time
import sys
import datetime
import json
import threading
import logging
import CodigoPWRMeterClick15 as PWRMeter
import schedule
import statistics as stats
import decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr


hora = datetime.datetime.now().isoformat()
dynamoDBresource = boto3.resource('dynamodb')

#PWRMeter.ValuesList = [None, None, None, None, None, None, None, None, None, None]

AlertSent = False

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO,  datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger('schedule').propagate = False
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('boto').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
#logging.getLogger('nose').setLevel(logging.CRITICAL)

#logging.basicConfig(format='%(levelname)s: %(asctime)s %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

#################### Flags ########################################

PublishThresholdsFlag  = False
PublishCalibrationFlag = False
RealTimeFlag 		   = False
DebugFlag 			   = False
StoreFlag			   = True
RealTimeAlertsFlag     = False

#################### Credentials to Access #########################

MQTT_HOST 					= "a1q9v3uypa506z-ats.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE 			= "C:/CertificadosAWSRaspberryPi/AmazonRootCA1.pem"
THING_CERT_FILE 			= "C:/CertificadosAWSRaspberryPi/certificate.pem.crt"
THING_PRIVATE_KEY			= "C:/CertificadosAWSRaspberryPi/private.pem.key"
MQTT_PORT 					= 8883
MQTT_KEEPALIVE_INTERVAL 	= 300
clientId 					= "Raspberry"  #Targeted client id

################### Topics #########################################

StoreTopic 		 	= 'PWRMeter/Store'              #Topico para publicar Valores en AWS IoT  (Para publicar python y subscribir android)
AlertTopic 		 	= "PWRMeter/Alerts"             #Topico para publicar Alertas en AWS IoT  (Para publicar python y subscribir android)
CalibrationTopic 	= "PWRMeter/Calibration"        #Topico para ejecutar Comandos de Calibracion (Desde App)  (Para publicar desde android)
ThresholdsTopic  	= "PWRMeter/Thresholds"         #Topico para ejecutar Comandos de Umbrales (Desde App)     (Para publicar desde android)
FixedCommandsTopic  = "PWRMeter/FixedCommands"      #Topico para ejecurar Fixed Commands   (Para publicar desde android)

ComsuptionTopic = 	  "PWRMeter/Comsuption"
ComsuptionAndroidTopic = "PWRMeter/Consumo"

CalibrationValuesTopic = "PWRMeter/Calibration/Values"   #Topico para enviar Valores de Calibracion y Confirmacion de comando hacia AWS IoT
ThresholdsValuesTopic  = "PWRMeter/Thresholds/Values"    #Topico para enviar Valores de Umbrales y Confirmacion de comando hacia AWS IoT

###### Topicos para publicar en android y subscribir en python  ######

RealSendLoopTopic = "PWRMeter/RealTime"	   #Topico para enviar valores en tiempo real (Para publicar desde Python y subscribir desde android)		
SelectModeTopic   = "PWRMeter/SelectMode"  #Topico para seleccionar modo  #Topico para cambiar modo de operacion (Para publicar desde Android y Subscribir en Python)

# def on_log(client, userdata, level, buf):
# #print("log: ",buf)

# # Define on_publish event function
# def on_publish(client, userdata, mid):
# #print ("Message Published at¨:" , datetime.datetime.now())

def on_subscribe(client, userdata, mid, granted_qos):

	logging.info("Subscripcion a temas realizadas correctamente")
######################## On_Messages Callbacks#######################

def SelectModeCallback(client, userdata, message):    ##Funcion para seleccionar modo de trabajo 

	global DebugFlag
	global RealTimeFlag
	global StoreFlag
	global RealTimeAlertsFlag
		
	decoded_message = message.payload.decode("utf-8")

	if(decoded_message == "Debug"):         #Se bloquea modo envio de datos y almacenamiento para ejecutar comandos

		RealTimeFlag = False
		StoreFlag    = False
		DebugFlag    = True
		logging.debug('Se ha entrado en modo debug para ajuste de parametros de sistema')	

	elif(decoded_message == "RealTime"):	#Se desactiva el modo debug y se habilita el envio de datos en tiempo real

		DebugFlag    = False
		StoreFlag    = False
		RealTimeFlag = True
		logging.debug('Medicion en tiempo real activada')

	elif(decoded_message == "Store"):		#Se desactiva el modo debug y se habilita el almacenamiento de datos

		DebugFlag    = False
		RealTimeFlag = False
		StoreFlag    = True
		logging.debug('Almacenamiento en base de datos activado')
		
	elif(decoded_message == "RealStore"):	#Se desactiva el modo debug y se habilitan el envio de datos en tiempo real y almacenamiento

		DebugFlag    = False
		RealTimeFlag = True
		StoreFlag    = True
		logging.debug('Medicion en tiempo real y almacenamiento en base de datos activados')
		
	elif(decoded_message == "SetRealAlerts"):

		RealTimeAlertsFlag = True
		logging.debug('Envio de alertas activado')

	elif(decoded_message == "NoRealAlerts"):

		RealTimeAlertsFlag = False
		logging.debug('Envio de alertas desactivado')

def SetThresholdsValuesCallback(client, userdata, message):
    
	if(DebugFlag == True):

		m_out = json.loads(message.payload)
		PWRMeter.SetEventsLimits( m_out['VSagLimit'] , m_out['VSurgeLimit'], m_out['OverCurrent'], m_out['OverPower'])
		upload = PWRMeter.ReadEventsLimits()	  
		

def SetCalibrationValuesCallback(client, userdata, message):
    
    if(DebugFlag == True):

    	m_out = json.loads(message.payload)
    	PWRMeter.SetCalibrationValues( m_out['VoltageCal'] , m_out['CurrentCal'] , m_out['PowerActCal'], m_out['PowerReactiveCal'], m_out['FreqCal'])
    	upload = PWRMeter.ReadCalibrationValues()

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
	logging.info('Ejecutando Thread Envio de datos en tiempo real')

	print(PWRMeter.ValuesList)

	while(True):

		if(RealTimeFlag == True):

			ValuesDict = { 'voltaje':   		PWRMeter.ValuesList[0],
                           'corriente': 		PWRMeter.ValuesList[1],
                           'potencia_activa':   PWRMeter.ValuesList[2], 
                           'potencia_reactiva': PWRMeter.ValuesList[3],
                           'potencia_aparente': PWRMeter.ValuesList[4],
                           'factor_potencia':   PWRMeter.ValuesList[7],
                           'frecuencia' : 		PWRMeter.ValuesList[5],
                           'temperatura' : 		PWRMeter.ValuesList[6],
                           'potencia_activa_consumida' : PWRMeter.ValuesList[8],
                           'potencia_consumida_reactiva' : PWRMeter.ValuesList[9]}

			mqttc.publish(RealSendLoopTopic, json.dumps(ValuesDict), qos=1)

		time.sleep(8)	

def RealTimeAlerts():

	global RealTimeAlertsFlag
	global AlertsDict
	global AlertSent
	logging.info('Ejecutando Thread Alertas en tiempo real')
	
	while(True):

		if(RealTimeAlertsFlag == True):

			RealAlerts = PWRMeter.ScanEvents()

			alert_time = datetime.datetime.now()

			AlertsDict = {'VSag'        :RealAlerts[0], 
						  'VSurge'      :RealAlerts[1], 
						  'OverCurrent' :RealAlerts[2], 
						  'OverPower'   :RealAlerts[3], 
						  'NoEvent'     :RealAlerts[4],
						  'year'        :"2019",
						  'fecha_hora'  :alert_time.strftime("%x %X"),						
						  'fecha' 		:alert_time.strftime("%x"),
						  'hora' 		:alert_time.strftime("%X")
						 }

			alertstatus =  PWRMeter.AlertLatch			  

			if(PWRMeter.AlertByte != 0x0):

				mqttc.publish(AlertTopic, json.dumps(AlertsDict), qos=1)

				AlertSent = True
				
		time.sleep(5)

############################### Schedule Functions ##############################################################################

def UploadDatabaseValues():
	
	datebase_time = datetime.datetime.now()

	if(StoreFlag == True):

		PromValues = {
						'voltajeprom'               : round( stats.mean( PWRMeter.ValuesSum[0] ), 2),
						'corrienteprom'             : round( stats.mean( PWRMeter.ValuesSum[1] ), 2),
						'potencia_act_prom'         : round( stats.mean( PWRMeter.ValuesSum[2] ), 2),
						'potenciareact_prom'        : round( stats.mean( PWRMeter.ValuesSum[3] ), 2),
						'potencia_app_prom'         : round( stats.mean( PWRMeter.ValuesSum[4] ), 2),
						'frecuenciaprom'            : round( stats.mean( PWRMeter.ValuesSum[5] ), 2),
						'temperaturaprom'           : round( stats.mean( PWRMeter.ValuesSum[6] ), 2),
						'factor_potencia_prom'      : PWRMeter.ValuesList[7],
						'potencia_accum_prom'       : PWRMeter.ValuesSum[8],
						'potencia_react_accum_prom' : PWRMeter.ValuesSum[9],
						'costo_dinero'				: round((PWRMeter.ValuesSum[8] * unit_cost), 2),
						'year'              		: "2019",						
						'fecha_hora'                : datebase_time.strftime("%x %X"),
						'fecha'                     : datebase_time.strftime("%x"),
						'hora'                      : datebase_time.strftime("%X"),
						# 'id_fechahora'              : hora.strftime("%x %X"),						
						# 'fecha'                     : hora.strftime("%x"),
						# 'hora'                      : hora.strftime("%X")  
						#'potencia_accum_react': PWRMeter.SumValues[8]
					 }

		mqttc.publish(StoreTopic, json.dumps(PromValues), qos=1)

		logging.info('Resultados medicion promedio: Voltaje: %.2f V, Corriente: %.2f A, Potencia Activa:  %.2f W, Potencia Reactiva:  %.2f VAr, {left_aligned:<15} Potencia Aparente:  %.2f Va,Frecuencia:  %.2f Hz, Temperatura:  %.2f, Energia consumida:  %.2f KWh , Energia Reactiva:  %.3f KVAr/H '
					 ,PromValues['voltajeprom'],PromValues['corrienteprom'],PromValues['potencia_act_prom'],PromValues['potenciareact_prom'],PromValues['potencia_app_prom'],PromValues['frecuenciaprom'],PromValues['temperaturaprom'],PromValues['potencia_accum_prom'], PromValues['potencia_react_accum_prom'])
		
		logging.info('Datos enviados a base de datos')

		for i in range(0,7):

			PWRMeter.ValuesSum[i].clear()


def GetUnitCost():

  table = dynamoDBresource.Table('Valores_Costos_Unitario')

  Unit_Costs = table.query(KeyConditionExpression = Key('Fecha').eq('17/07/2019 19:23:00'))

  G  = Unit_Costs['Items'][0]['G']
  T  = Unit_Costs['Items'][0]['T']
  D  = Unit_Costs['Items'][0]['D']
  PR = Unit_Costs['Items'][0]['PR']
  R  = Unit_Costs['Items'][0]['R']
  C  = Unit_Costs['Items'][0]['C']

  Unit_Cost = float(G+T+D+PR+R+C)

  print(Unit_Cost)

  return Unit_Cost

def GetComsuption(client, userdata, message):

	decoded_message = message.payload.decode("utf-8")

	if(decoded_message == "GetConsumption"):

		consumo = PWRMeter.ValuesSum[8]

		ComsuptionDict = {'consumo'		: consumo,
					  	  'costo_dinero': round((consumo * unit_cost), 2) 
					 	 } 

		mqttc.publish(ComsuptionAndroidTopic, json.dumps(ComsuptionDict), qos=1)

	logging.info('Datos de consumo enviados')
			
# MQTT init and Connect
mqttc = mqtt.Client()
#mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# mqttc.on_log = on_log
mqttc.tls_set(ca_certs=CA_ROOT_CERT_FILE,
			  certfile=THING_CERT_FILE, 
			  keyfile=THING_PRIVATE_KEY,
			  cert_reqs=ssl.CERT_REQUIRED, 
			  tls_version=ssl.PROTOCOL_TLSv1_2,
			  ciphers=None)

mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

unit_cost = GetUnitCost()

logging.info('Conectado a AWS IoT')

######################## Subscribe to Topics######################

mqttc.subscribe([ (FixedCommandsTopic,1),
				  (ThresholdsTopic,1),
				  (CalibrationTopic,1),
				  (RealSendLoopTopic,1),
				  (SelectModeTopic,1),
				  (ComsuptionTopic,1)
				])

mqttc.message_callback_add(FixedCommandsTopic, FixedCommandsCallBack)
mqttc.message_callback_add(ThresholdsTopic, SetThresholdsValuesCallback)
mqttc.message_callback_add(CalibrationTopic, SetCalibrationValuesCallback)
mqttc.message_callback_add(SelectModeTopic, SelectModeCallback)
mqttc.message_callback_add(ComsuptionTopic, GetComsuption)
mqttc.loop_start()

##################### Set Schedule Jobs ###################################################################

schedule.every(20).minutes.do(UploadDatabaseValues)
schedule.every(15).minutes.do(PWRMeter.SaveEnergyCounters)

################################ Thread Functions Init #####################################################

hilo1 = threading.Thread(target=RealTimeValues)
hilo2 = threading.Thread(target=RealTimeAlerts)

hilo1.start()
hilo2.start()

#PWRMeter.LatchEvents(False,False,True,False)

time.sleep(2)

################################ 

try:

	while(True):

		if(DebugFlag == False):
		
			schedule.run_pending()

			PWRMeter.GetValues()

		if(StoreFlag == True and DebugFlag==False):

			PWRMeter.SumValues()

		if(AlertSent == True and DebugFlag==False):

			PWRMeter.ClearEvents()

			AlertSent = False

		time.sleep(0.1)

		# # if(RealTimeAlertsFlag == True):

		# # 	RealTimeAlerts()
		
except KeyboardInterrupt:

	print("Programa Finalizado por Usuario ")


