#!/bin/bash

#update firmware

DOWNLOADDIR="/home/firmware"
UPDATESTATUS="/home/ubuntu/update_status"
#FIRMWARE=$(ls /home/download/ | grep firmware)

if [ ! -f "${UPDATESTATUS}" ]
then
	echo "not find update status file"
	exit
fi

sta=$(cat ${UPDATESTATUS} | awk -F":" '{print $1}')
version=$(cat ${UPDATESTATUS} | awk -F":" '{print $2}')
FIRMWARE="/home/download/firmware_${version}.des3.tar.gz"
if [ ! -f "${FIRMWARE}" ]
then
	echo "not find firmware:${FIRMWARE}"
	echo "error:${version}:1" > ${UPDATESTATUS}
	exit
fi

ret=$(which rsync)
if [ -z "${ret}" ]
then
	apt-get install rsync
fi

kill_little_watchdog() {
	pid=$(ps -ef | grep little_feed | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then 
		kill -9 ${pid}
	fi
}

update_start() {
	#1.close monitor script and mqtt client process
	#  start_network.sh must keep running,beacuse feed watchdog in this process
	echo "start update"
	#/root/watch.sh zywlmonitor.sh stop
	#/root/watch.sh mqtt stop
	systemctl stop zywldl
	#2.show update image
	python3 /root/showimage.py 4
	echo "tarfile:${version}:0" > ${UPDATESTATUS}
}

tarfile() {
	echo "tar file"
	if [ -d "${DOWNLOADDIR}.back" ]
	then 
		rm -rf "${DOWNLOADDIR}.back"
	fi

	if [ -d "${DOWNLOADDIR}" ]
	then
		mv ${DOWNLOADDIR} ${DOWNLOADDIR}.back
	fi

	mkdir -p ${DOWNLOADDIR}

	sync
	while true
	do
		dir=$(pwd)
		if [ "${dir}" != "${DOWNLOADDIR}" ]
		then
			mkdir -p ${DOWNLOADDIR}
			cd ${DOWNLOADDIR}
		else
			break
		fi
	done
	
	#该文件必须首先要存在/root目录下才能解压
	python3 /root/uncompress.py ${FIRMWARE} ${DOWNLOADDIR}
	if [ ! -d "${DOWNLOADDIR}/target" ]
	then
		echo "tar firmware:${FIRMWARE} failed"
		echo "error:${version}:2" > ${UPDATESTATUS}
		exit
	fi

	sleep 1
	rsync ${DOWNLOADDIR}/target/shell/little_feed.sh /home/watchdog
	#rsync python feed watchdog script to /home/watchdog
	rsync -r ${DOWNLOADDIR}/target/watchdog/ /home/watchdog
	echo "move:${version}:0" > ${UPDATESTATUS}
}

move() {
	echo "move file"
	cd /root
	if [ ! -d "${DOWNLOADDIR}/target" ]
	then 
		echo "move file error!"
		echo "error:${version}:3" > ${UPDATESTATUS}
	else
		#删除只存在于/root中，不存在于更新包中的文件
		#/root/watch.sh stop
		systemctl stop zywldl
		sleep 1
		/home/watchdog/little_feed.sh &
		
		#rsync python modules
		rsync -r ${DOWNLOADDIR}/target/python/*.so /usr/local/lib/python3.5/dist-packages/

		#rsync shell script to /root
		rsync -r ${DOWNLOADDIR}/target/shell/*.sh /root/
		
		#rsync python run script to /root
		rsync -r ${DOWNLOADDIR}/target/run/*.py /root/
		
		#rsync image file to /root
		rsync -r ${DOWNLOADDIR}/target/image /root/
		
		#rsync image file to /root
		rsync -r ${DOWNLOADDIR}/target/ppp/ /etc/ppp

		#config file rsync
		if [ ! -f "/root/net.conf" ]
		then
			cp ${DOWNLOADDIR}/target/net.conf /root
		fi

		if [ ! -f "/root/config.ini" ]
		then
			cp ${DOWNLOADDIR}/target/config.ini /root
		fi

		rsync -r ${DOWNLOADDIR}/target/ntp.conf /etc/
		
		#crtfile rsync
		mkdir -p /root/crtfile
		rsync -r ${DOWNLOADDIR}/target/*.crt /root/crtfile/

		if [ ! -d "/root/log" ]
		then
			mkdir -p /root/log
		fi

		#install frpc service
		rsync -r ${DOWNLOADDIR}/target/frp/systemd/* /lib/systemd/system/
		rsync -r ${DOWNLOADDIR}/target/frp/frpc /usr/bin/
		rsync -r ${DOWNLOADDIR}/target/frp/frpc.ini /etc/frp/
		systemctl enable frpc

		#ver=${FIRMWARE#*_}
		#ver=${ver%%.*}
		/root/set_config.sh "version " " ${version}"
		/root/set_config.sh "VERSION" "${version}"

		rsync ${DOWNLOADDIR}/target/rc.local /etc/

		echo "clear:${version}:0" > ${UPDATESTATUS}
	fi
}

update_clear() {
	echo "clear file"
	cd /root
	rm /home/download/*
	echo "done:${version}:0" > ${UPDATESTATUS}
	sync
	kill_little_watchdog
	sleep 1
	#/root/watch.sh restart
	systemctl restart zywldl
}

if [ -n "${sta}" ]
then
	case ${sta} in 
	"start")
		update_start	
		tarfile
		move
		update_clear
	;;
	"tarfile")
		tarfile
		move
		update_clear
	;;
	"move")
		move
		update_clear
	;;
	"clear")
		update_clear
	;;
	*)
	;;
	esac
fi
