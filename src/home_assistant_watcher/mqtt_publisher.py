import paho.mqtt.client as mqtt

class MQTTPublisher:
    def __init__(self, broker_host="localhost", broker_port=1883, client_id=None, username=None, password=None):
        self.client = mqtt.Client(client_id=client_id)
        if username and password:
            self.client.username_pw_set(username, password)
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.connected = False
        
    def connect(self):
        if not self.connected:
            self.client.connect(self.broker_host, self.broker_port)
            self.client.loop_start()
            self.connected = True
            
    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            
    def publish(self, topic, payload, qos=0, retain=False):
        if not self.connected:
            self.connect()
        self.client.publish(topic, payload, qos, retain)