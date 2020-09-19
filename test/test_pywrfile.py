

with open("./net.conf", "r+") as f:
	s = f.readline()
with open("./net.conf", "w") as f:
	f.write("{}ssid={}\npsk={}\n".format(s, "duanshuai" , "1929392193219"))
