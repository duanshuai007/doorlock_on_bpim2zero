## OS Wifi 2G 网络设置

经过测试筛选，最终选择了`2020-04-28-debian-9-stretch-lite-bpi-m2z-sd-emmc.img`。

下载链接: `https://pan.baidu.com/s/1pJfJbhIcU52uaR4mkWc-4A Pincode：5e3E`

## Wifi网络设置

在该系统内部集成了wpa网络管理模块，可以使用wpa_cli命令对网络进行设置。
也可以使用配置文件的方式使wpa模块启动后自动连接指定的Wi-Fi。

### 1.配置文件方式启动
	
通过`wpa_passphrase ssid psk > /etc/wpa.conf `将wifi配置信息生成输出到配置文件中。在`/etc/rc.local`文件中加入开机启动程序，`wpa_supplicant -iwlan0 -c /etc/wpa.conf`。

### 2.通过wpa_cli命令行设置

首先将配置`wifi`的脚本放在`/root/`目录下，脚本`start_wifi.sh`内容如下。

```
wpa_cli -iwlan0 add_n
该指令会根据网络列表中的个数自动递增，因为没有配置wpa.con文件，所以默认是0

该指令设置Wifi名
wpa_cli -iwlan0 set_n 0 ssid \"Frog\"

设置Wifi密码
wpa_cli -iwlan0 set_n 0 psk \"password\"

启动wifi
wpa_cli -iwlan0 select_n 0
wpa_cli -iwlan0 enable_n 0
```

然后设置开机启动脚本,在/etc/rc.local文件中加入
`/root/start_wifi.sh`

## 2G网络设置

开发板通过SIM800C连接2G网络，我们使用PPPD来对其进行管理。

### 1.安装pppd

首先去`http://git.ozlabs.org/?p=ppp.git;a=summary`网页选择`ppp-2.4.8`版本进行下载。

下载完成后将源码通过scp方式上传到开发板上。

解压源码  
`tar -zxvf ppp-78cd384.tar.gz`

编译源码。

```
cd ppp-78cd384
./configure
make
make install
```

安装完成后还需要编写`pppd`控制脚本。
首先在`/etc/`目录下新建文件夹`ppp`然后在`ppp`文件中新建文件夹`peers`,然后在`peers`目录中分别创建`myapp, myppp-chat-connect, myppp-chat-disconnect`三个脚本。

myapp脚本

```
#/etc/ppp/peers/file_name

# Usage: root> pppd call file_name

# 调试时隐藏密码
hide-password

# 该手机不需要身份验证
noauth

#############################################
# 注意: 这里要知道chat安装的位置, 如果不在环境变量
# 里面, 则要指定位置(如 /usr/sbin/chat -s -v -f)
#############################################
# 用于呼叫控制脚本
connect 'chat -s -v -f /etc/ppp/peers/myppp-chat-connect'

# 断开连接脚本
disconnect 'chat -s -v -f /etc/ppp/peers/myppp-chat-disconnect'

# 调试信息
debug

# 模块串口设备
/dev/ttyS2

# 串口波特率
115200

# 使用默认路由
defaultroute 

# 不能指定默认IP
noipdefault 

# No ppp compression 
novj 
novjccomp 
noccp 
ipcp-accept-local 
ipcp-accept-remote 
local 

# 最好锁定串行总线
lock
dump

logfile /var/log/ppplogfile
#停留在后台监视网络，一旦有需求就立即联网
demand
#永久链接，自动重播
persist
nodetach
# Keep pppd attached to the terminal 

# 用户名 密码
# user root
# password

# 硬件控制流
crtscts
remotename 3gppp
ipparam 3gppp

# 向对方请求最多2个DNS服务器地址
usepeerdns

```

myppp-chat-connect

```
TIMEOUT 15
# 连续15秒, 收到以下字符, 退出执行
ABORT   "BUSY" 
ABORT   "NO CARRIER" 
ABORT   "NO DIALTONE" 
ABORT   "ERROR" 
ABORT   "NO ANSWER" 

TIMEOUT 20
# 40秒内没有收到指定字符, 退出
# 如: OK \rATZ, 发送 ATZ, 希望收到的是 OK.
'' AT  
SAY "\nCheck SIM80)\n" 
OK \rATZ
SAY "\nCheck SIM800 active\n" 
OK ATE1

#cmnet 是移动的接入点 3gnet是联通3g接入点。
OK \rAT+COPS?
'CHINA MOBILE' \rAT+CGDCONT=1,"IP","cmnet",,0,0

OK AT+CGQREQ=1,0,0,0,0,0
OK AT+CGQMIN=1,0,0,0,0,0

# 拨号
OK \rAT+COPS?
'CHINA MOBILE' ATDT*99***1#  
SAY "\nWaiting for connect...\n"
CONNECT ""  
SAY "\nConnected!"
```


myppp-chat-disconnect

```
ABORT "ERROR" 
ABORT "NO DIALTONE" 
SAY "\NSending break to the modem\n"
""\k"
""+++ATH" 
SAY "\nGood bye !\n"
```


设置pppd开机启动

在/etc/rc.local文件中加入

`pppd call myapp &` 这样就会开机启动脚本。

## 开机启动网络管理脚本

将pppd和wifi网络的启动放在一个脚本文件中进行统一管理，通过设置为后台守护进程一直监视进程保证进程执行。  
去掉`/etc/rc.local`中关于`pppd`和`wpa`的语句，然后加入`/root/start_network.sh &`，脚本内容如下.

```
#!/bin/bash

#开机启动脚本，启动wpa 和 pppd线程

PPPD=$(which pppd)

while true
do
	ps -ef | grep wpa_supplicant | grep -v grep > /dev/null
		if [ $? -ne 0 ] 
		then 
			ifconfig | grep wlan0 > /dev/null
			if [ $? -ne 0 ]
			then
				#equl 1 mean wlan0 not exists
				/sbin/wpa_supplicant -iwlan0 -c /etc/wpa.conf > /var/log/wpalog 2>&1 &
				sleep 1
				dhclient wlan0
			fi
		fi

	ps -ef | grep pppd | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		${PPPD} call myapp &
	fi

	sleep 10
done
```

