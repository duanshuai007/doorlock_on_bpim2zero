#!/bin/bash

firmware_path=$1

if [ -z "${firmware_path}" ]
then
	echo "must enter firmware path"
	exit
fi

if [ -f "/root/watch.sh" ]
then
	/root/watch.sh stop
fi

systemctl stop zywldl

cp ${firmware_path}/python/*	/usr/local/lib/python3.5/dist-packages/
cp ${firmware_path}/shell/*		/root/
cp ${firmware_path}/run/*		/root/
cp ${firmware_path}/config.ini	/root/
cp -r ${firmware_path}/image	/root/
cp ${firmware_path}/net.conf	/root/

cp -r ${firmware_path}/watchdog /home/

cp ${firmware_path}/ntp.conf	/etc/

mkdir -p /root/crtfile
cp ${firmware_path}/mqtt.iotwonderful.cn.crt /root/crtfile

#install frp client
mkdir -p /etc/frp
cp ${firmware_path}/frp/frpc		/usr/bin/
cp ${firmware_path}/frp/frpc.ini	/etc/frp/
cp ${firmware_path}/frp/systemd/*		/lib/systemd/system/

#install pppd
cp -r ${firmware_path}/ppp			/etc

if [ ! -f "/usr/bin/zywldl" ]
then
	ln -s /root/watch.sh /usr/bin/zywldl
fi

cp ${firmware_path}/systemd/zywldl.service	/lib/systemd/system/
systemctl enable zywldl

