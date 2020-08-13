## OS Wifi 2G 网络设置

经过测试筛选，最终选择了`2020-04-28-debian-9-stretch-lite-bpi-m2z-sd-emmc.img`。

下载链接: `https://pan.baidu.com/s/1pJfJbhIcU52uaR4mkWc-4A Pincode：5e3E`

## Wifi网络设置

在该系统内部集成了wpa网络管理模块，可以使用wpa_cli命令对网络进行设置。
也可以使用配置文件的方式使wpa模块启动后自动连接指定的Wi-Fi。

### 1.配置文件方式启动
	
通过`wpa_passphrase ssid psk > /etc/wpa.conf `将wifi配置信息生成输出到配置文件中。  
在`/etc/rc.local`文件中加入开机启动程序，`wpa_supplicant -iwlan0 -c /etc/wpa.conf`。

### 2.通过wpa_cli命令行设置

首先将配置`wifi`的脚本放在`/root/`目录下，脚本`connect_wifi.sh`内容如下。

```
#!/bin/bash

SSID=$1
PASSWORD=$2

if [ -z "${SSID}" -o -z "${PASSWORD}" ]
then
        echo "parameters error"
        echo "please run script like this:"
        echo "./script.sh ssid password"
        exit
fi

#np=$(wpa_cli -iwlan0 add_n)
np=0
#?该?指?令?会?根?据?网?络?列?表?中?的?个?数?自?动?递?增?，??帺?没?有?配?置wpa.con?文?件?，?所?以?默?认?是0
wpa_cli -iwlan0 disable_n ${np} > /dev/null 2>&1
#?该?指?令?设?置Wifi?名
wpa_cli -iwlan0 set_n ${np} ssid \"${SSID}\" > /dev/null 2>&1

#?设?置Wifi?密?码
wpa_cli -iwlan0 set_n ${np} psk \"${PASSWORD}\" > /dev/null 2>&1

#?启?动wifi
wpa_cli -iwlan0 select_n ${np} > /dev/null 2>&1
wpa_cli -iwlan0 enable_n ${np} > /dev/null 2>&1
```

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

## 硬件控制

#### 控制GPIO

控制gpio有两种方式

* 1 使用python的mmap库对内存进行映射，然后直接对寄存器就可以进行读写控制。通过这种方式实现了对PA3引脚的读写。

* 2 编写驱动程序引脚进行控制，使用`gpio_request，gpio_set_value,gpio_get_value`等内核函数对gpio进行读写操作，并传递到用户空间。


#### 控制SPI

在BPIM2-zero中有两个spi，其中spi0是默认提供的spi接口，linux还提供了一个通用驱动程序spidev.c，我们的设备接在了spi1上，无法直接使用Linux的spi驱动，所以选择使用字符设备驱动读写寄存器的方式来对spi进行控制。




## 设置开机启动

通过`/etc/rc.local`的方式设置开机启动已经逐渐被弃用，本文中使用`systemctl`的方式来设置开机启动。  
通过编写一个`service`来把我们的程序加入到开机启动，并可以通过`systemctl`进行`start,stop,restart`等操作。

本工程一共实现了3个`service`，分别是`zywldl`、`zywlpppd`和`zywlmqtt`.

- `zywldl`:`正(z)源(y)物(w)联(l)门(d{oor})锁(l{ock})`的简称。该服务为整个工程的开始和停止服务，需要设置为开机启动。该服务能够正常使用的前提是在`/usr/bin/`目录下生成`watch.sh`的链接`ln -s /root/watch.sh /usr/bin/zywldl`,并且将`zywldl.service`文件放入`/lib/systemd/system/`目录下。执行`systemctl enable zywldl`使能开机启动功能。
- `zywlpppd`:该服务是用来检测`gsm`模块内是否有`sim`卡，识别卡的类型，并将对应的`pppd connect`文件复制到`/etc/ppp/peers/`目录下。启动与停止完全由`zywldl`服务来控制，不需要开机启动。
- `zywlmqtt`:改脚本是用来控制`mqtt`客户端程序的开启和停止。启动与停止完全由`zywldl`服务来控制，不需要开机启动。

* 也可以通过`systemctl start/stop zywldl/zywlpppd/zywlmqtt`来控制对应服务的启停。
* 通过`systemctl status zywldl/zywlpppd/zywlmqtt`来查询对应服务的状态。  

## 烧写镜像的方法

### 1.拷贝镜像到本地

sudo bpi-copy /dev/sdb ubuntu.img 7296


### 2.烧写镜像到sd卡

sudo bpi-copy ubuntu.img /dev/sdb 7296


## 修改镜像大小的方法

```
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
```

## 监视所有设备
代码参考`test/mqtt_publish.py`文件  
`python3 mqtt_publish.py`

## 获取已知设备sn的设备ip
代码参考`test/mqtt_publish_deviceinfo.py`文件。  
`python3 mqtt_publish_deviceinfo.py [device sn] [doorlock]`    

- `device sn`: all表示获取所有在线设备的信息, 若填入具体的设备sn则表示只查询或设置该单独设备。
- doorlock: 0表示读取doorlock time， 其他大于0的值表示将设备的doorlock time设置为该值

## 上传代码压缩包到服务器
代码参考`test/firmware_upload.py`文件  
`python3 firmware_upload.py  [firmware path]`   
执行后会返回

```
swann@ubuntu:~/workgit/acs/test$ python3 firmware_upload.py ../firmware_10.des3.tar.gz 
0
upgrade/0c17816d.
```
其中0表示升级成功，最下面的则是对应该文件的链接。

## 增加了在线升级功能
代码参考`test/mqtt_publish_update.py`文件。
`python3 mqtt_publish_update.py [device sn] [download] [md5] [version]`  

- download:程序代码的下载地址，该地址只需要填入上一步中获取的文件链接地址`upgrade/0c17816d.`即可。
- md5:程序代码压缩包的md5校验值，通过shell命令md5sum firmware来获取。 
- version:程序代码的版本信息，如果目标板的版本信息大于等于version，则不进行升级操作。  

## 增加了ssh内网穿透功能

代码参考`test/mqtt_publish_enablessh.py`文件。
`python3 mqtt_publish_enablessh.py [device sn] [enable]`

- enable = 1 表示打开ssh  enable = 0 表示关闭ssh  
- 返回的信息中`status="open"` 表示打开成功，`status="close"` 表示关闭成功

## 控制门锁开关

代码参考`test/mqtt_publish_ctrlled.py`文件  
`python3 mqtt_publish_ctrlled.py [device sn] [switch]`  

- switch: 1表示开启门锁， 0表示关闭门锁。
- 开启门锁后，门锁会在[doorlock time]时间后自动关闭


## 设置板子上的wlan

代码参考`/test/mqtt_publish_wlan.py`文件  
`python3 mqtt_publish_wlan.py [device sn] [ssid] [psk]`  

- ssid:设置wifi的名
- psk:设置wifi的密码
- 设置wifi后，如果目标板子只能通过wifi上网，则一定要谨慎执行该指令，否则可能导致无法连接到板子上。


## 测试生成二维码
代码参考`/test/mqtt_publish_qrreq_3.py`文件   
`python3 mqtt_publish_qrreq_3.py [device sn] [qr message]`   

