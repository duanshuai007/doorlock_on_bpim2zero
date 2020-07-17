import config

c = config.config("./config.ini")
print(c.get("MQTT", "USER"))
