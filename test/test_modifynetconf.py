import os

ssid="testssid"
psk="testpsk"
shellcmd = "./set_current_wifi.sh wlan {} {}".format(ssid, psk)
print(shellcmd)
os.system(shellcmd)
retssid = os.popen("cat ./net.conf | grep ssid | awk -F\"=\" '{print $2}'").read().split('\n')[0]
retpsk = os.popen("cat ./net.conf | grep psk | awk -F\"=\" '{print $2}'").read().split('\n')[0]
print("{} {}".format(retssid, retpsk))
if retssid == ssid and retpsk == psk:
	print("write success")
