## 1.硬件配置

||BPI-M2 Zero|
|:-:|:-:|
|CPU| H2+ Quad-core Cortex-A7 |
|GPU| Mali 400 MP2 |
|内存| 512M DDR3 |
|存储支持| MicroSD插槽 |
|板载网络| Wi-Fi 802.11 b/g/n<br>蓝牙 4.0|
|视频输出| Mini HDMI |
|音频输出| Mini HDMI |
|USB接口| 1xUSB 2.0 OTG|
|GPIO| GPIO(x28) <br>供电(+5V,+3.3V,GND)<br>UART,I2C,SPI or PWM|
|电源输入|Micro USB(5V2A)|
|系统| Linux |
|SD卡| 8GB |

|显示模块|DV160160A-A4|
|:-:|:-:|
|接口|SPI|
|供电|+3.3V,GND|
|驱动点阵数|160x160|
|显示内容|160x160点阵单色图片|
|外形尺寸|83.8(L) X 76.5(W) X 8.8(T)|
|可视区域|60.0(L) X 60.0(W)|
|功耗|带背光电流在80ma以内|

|2G模块|SIM800C|
|:-:|:-:|
|接口|UART,使用AT指令集|
|供电|+5V,GND|

## 2.系统镜像的选择

对比了
`2020-04-28-ubuntu-16.04-server-bpi-m2z-sd-emmc.img`,   
`2020-04-28-debian-9-stretch-lite-bpi-m2z-sd-emmc.img`,   
`2020-04-10-raspbian-jessie-ap6212-bpi-m2z-sd-emmc.img`,   
`bananapi-m2z-8GB.img`  
这四个镜像.

||2020-04-28-ubuntu-16.04-server-bpi-m2z-sd-emmc.img|2020-04-28-debian-9-stretch-lite-bpi-m2z-sd-emmc.img|2020-04-10-raspbian-jessie-ap6212-bpi-m2z-sd-emmc.img|bananapi-m2z-8GB.img|
|:-:|:-:|:-:|:-:|:-:|
|镜像大小|7.1G|7.1G|7.1G|7.4G|
|系统内程序空间占用的大小|2G|2G|2G|200MB+|
|系统启动时间|1分钟|1分钟|1分钟|1分钟|
|系统稳定性|偶尔会出现崩溃，复位重启或上电重启时会出现异常导致无法进入系统**(x)**|未测试|未测试|经测试每次都能正常进入系统|
|程序中所使用的硬件资源|具有满足程序所使用到的所有硬件驱动|串口不具备**(x)**|串口不具备**(x)**|具有满足程序所使用到的所有硬件驱动|
|能够编译内核驱动|能|未测试|未测试|因为没有内核源码，无法编译内核驱动|
|下载地址|`https://drive.google.com/drive/folders/1uRE8BppgDjK2TXH5kUIJ1_YrbAAW3HKF`|-|-|`https://mega.nz/#!obIAVQiA!G0CCABkLunCcG8hEqMf7NfjTBK1jgMytt2f0VdtOl08`|

##### 表格中x为该镜像不使用的原因

在`bananapi-m2z-8GB.img`系统中，经过调查研究发现，没有内核源码的情况，可以通过mmap的方式来对硬件gpio进行控制，从而实现模拟spi的功能，在性能上与通过编写内核驱动控制gpio的速率几乎没有区别。所以最后选择了该镜像。  
关于该镜像的文章:`https://github.com/avafinger/bananapi-zero-ubuntu-base-minimal`  



