

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import ssl
import time
import sys
import datetime
import json
import threading

MQTT_HOST = "a1q9v3uypa506z-ats.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "C:/CertificadosAWSRaspberryPi/AmazonRootCA1.pem"
THING_CERT_FILE = "C:/CertificadosAWSRaspberryPi/certificate.pem.crt"
THING_PRIVATE_KEY = "C:/CertificadosAWSRaspberryPi/private.pem.key"
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 300
clientId = "Raspberry"


Topic_one = "PWRMeter/Prueba1"
Topic_two = "PWRMeter/Prueba2"

def on_log(client, userdata, level, buf):
    print("log: ",buf)

# Define on_publish event function
def on_publish(client, userdata, mid):
	print ("Message Published at¨:" , datetime.datetime.now())

def on_subscribe(client, userdata, mid, granted_qos):

	print("Suscrito a tema correctamente")

mqttc = mqtt.Client()

# Register publish callback function
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_log = on_log

mqttc.tls_set(ca_certs=CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

mqttc.loop_start()


def FuncionHilo2():

	while(True):

		Values2= {"Valor1": 31231225234, "Valor2": str(datetime.datetime.now()) , 
				 "Valor3": False}

		time.sleep(10)


		ValuesJSon2 =  json.dumps(Values)
		mqttc.publish(Topic_two,ValuesJSon2,qos=1)

hilo2 = threading.Thread(target=FuncionHilo2 )

hilo2.start()

while(True):

	Values= {"Valor1": 31231, "Valor2": str(datetime.datetime.now()) , 
			 "Valor3": True}
	ValuesJSon =  json.dumps(Values)
	mqttc.publish(Topic_one,ValuesJSon,qos=1)

	time.sleep(600)