# Import package
import paho.mqtt.client as mqtt
import ssl
import time
import sys
import datetime

# Define Variables
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 600
MQTT_TOPIC = "helloTopic"
MQTT_MSG = "hello MQTT"

MQTT_HOST = "a1q9v3uypa506z-ats.iot.us-west-2.amazonaws.com"
CA_ROOT_CERT_FILE = "C:/CertificadosAWSRaspberryPi/AmazonRootCA1.pem"
THING_CERT_FILE = "C:/CertificadosAWSRaspberryPi/certificate.pem.crt"
THING_PRIVATE_KEY = "C:/CertificadosAWSRaspberryPi/private.pem.key"


# Define on_publish event function
def on_publish(client, userdata, mid):
	print ("Message Published at¨:" , datetime.datetime.now())


# Initiate MQTT Client
mqttc = mqtt.Client()

# Register publish callback function
mqttc.on_publish = on_publish

# Configure TLS Set
mqttc.tls_set(ca_certs=CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)		
mqttc.loop_start()

counter = 0

try:
	while True:
	 	mqttc.publish(MQTT_TOPIC,MQTT_MSG + str(counter),qos=1)
	 	counter += 1
	 	time.sleep(5)

	# Disconnect from MQTT_Broker
	#mqttc.disconnect()

except KeyboardInterrupt:

	print("Programa Finalizado por ")