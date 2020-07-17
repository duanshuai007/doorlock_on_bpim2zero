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

## 开机启动网络管理脚本

将pppd和wifi网络的启动放在一个脚本文件中进行统一管理，通过设置为后台守护进程一直监视进程保证进程执行。  
去掉`/etc/rc.local`中关于`pppd`和`wpa`的语句，然后加入

```
/root/start_network.sh &
/root/monitor_network.sh &
```


## 硬件控制

#### 控制GPIO

控制gpio有两种方式

* 1 使用python的mmap库对内存进行映射，然后直接对寄存器就可以进行读写控制。通过这种方式实现了对PA3引脚的读写。

* 2 编写驱动程序引脚进行控制，使用gpio_request，gpio_set_value,gpio_get_value等内核函数对gpio进行读写操作，并传递到用户空间。


#### 控制SPI

在BPIM2-zero中有两个spi，其中spi0是默认提供的spi接口，linux还提供了一个通用驱动程序spidev.c，我们的设备接在了spi1上，无法直接使用Linux的spi驱动，所以选择使用字符设备驱动读写寄存器的方式来对spi进行控制。

最后在/root目录下执行`pyhthon3 mqtt_client.py`启动客户端程序。

* log信息输出在/root/log/server.log文件中


## 修改/etc/rc.local

使用eth0的mac地址作为设备的id.
```
python3 /root/showimage.py 1
/root/start_network.sh &
/root/get_eth0_mac.sh
/root/monitor_network.sh &
```

## 烧写镜像的方法

### 1.拷贝镜像到本地

sudo bpi-copy /dev/sdb ubuntu.img 7296


### 2.烧写镜像到sd卡

sudo bpi-copy ubuntu.img /dev/sdb 7296


## 修改镜像大小的方法

1.首先sd卡插入读卡器，连接到电脑上。  
执行mount命令，会发现/dev/sdx1 /dev/sdx2的挂载点。  

2.  
umount /dev/sdx1  
umount /dev/sdx2  

3.
dd if=/dev/sdx of=test.img

4.
sudo modprobe loop  
sudo losetup -f  
这是会返回`/dev/loop0`

sudo losetup /dev/loop0 test.img

sudo partprobe /dev/loop0

sudo gparted /dev/loop0  


在图形界面工具中，调整分区的大小。
调整完毕后几的点几apply按钮保存配置。


sudo losetup -d /dev/loop0

fdisk -l test.img

	Disk test.img: 28.8 GiB, 30908350464 bytes, 60367872 sectors
	Units: sectors of 1 * 512 = 512 bytes
	Sector size (logical/physical): 512 bytes / 512 bytes
	I/O size (minimum/optimal): 512 bytes / 512 bytes
	Disklabel type: dos
	Disk identifier: 0xcaaba8e3
	Device     Boot  Start      End Sectors  Size Id Type
	test.img1        49152   253951  204800  100M 83 Linux
	test.img2       253952 10113023 9859072  4.7G 83 Linux
最后执行以下命令，镜像就会变成修改的大小了。
sudo truncate --size=$[(10113023+1)*512] test.img

## 获取已知设备sn的设备ip

在没有串口线的情况下通过mqtt来获取设备ip

订阅topic:`/test/device_info_resp`

生成数据

```
sendmsg = 
{
	"device_sn" : "", 
	"stime" : 0,
	# 0  = get doorlock time
	# !0 = set doorlock time
	"doorlock" : 0,
	"ip" : "", 
	"current" : "", 
	"thread status" : ""
}
```

填充`device_sn`以及`stime`，在python3脚本程序中`stime=int(time.time())`  
如果不想修改`doorlock`时间，则该项一定要设置为0  
然后将数据转换为bytes  
json.dumps(sendmsg)  
然后通过mqtt 将该信息publish 到 `/test/device_info` 该主题上。

通过订阅信息就能接收到返回的信息

```
on message:/test/device_info_resp 0 b'{"current": "eth0", "doorlock": "success", "stime": 0, "device_sn": "024251720577", "thread status": "", "ip": "192.168.200.54"}'
```
就获得了设备的ip地址，就可以通过ssh登陆了(仅限于内网)。

也可以通过该条信息来设置`doorlock`的时间。

```
当doorlock = 0 时，程序查询设备上的doorlock时间，并通过信息返回。
当doorlock 不等于 0 时，程序会将doorlock的值设置为本地的doorlock时间，成功返回success，失败返回failed
设置的doorlock立即生效
```

## 增加了在线升级功能

升级topic:`/update`
响应topic:`/update_resp`

```
"device_sn" : "",
	"stime" : "",
	"firmware" : {
		"url" : "",
		"version" : "",
		"packetsize" : 0,
		"enable" : "",
		"md5" : "",
	}
```

## 增加了ssh内网穿透功能

设置topic:`/ssh_enable`
响应topic:`/ssh_enable_resp`

```
sendmsg = 
{
	"device_sn" : "", 
	"stime" : "", 
	"enable" : 0,
	"opentime" : 0,
}
```
填充`device_sn`以及`stime`，在python3脚本程序中`stime=int(time.time())`     
enable = 1 表示打开ssh  
enable = 0 表示关闭ssh  
返回的信息中`status="open"` 表示打开成功，`status="close"` 表示关闭成功


