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

update_start() {
	python3 /root/showimage.py 4
	echo "tarfile:${version}:0" > ${UPDATESTATUS}
}

tarfile() {
	if [ -d "${DOWNLOADDIR}.back" ]
	then 
		rm -rf "${DOWNLOADDIR}.back"
	fi

	if [ -d "${DOWNLOADDIR}" ]
	then
		mv ${DOWNLOADDIR} ${DOWNLOADDIR}.back
	fi

	mkdir -p ${DOWNLOADDIR}

	#该文件必须首先要存在/root目录下才能解压
	python3 /root/uncompress.py ${FIRMWARE} ${DOWNLOADDIR}
	if [ ! -d "${DOWNLOADDIR}/target" ]
	then
		echo "tar firmware:${FIRMWARE} failed"
		echo "error:${version}:2" > ${UPDATESTATUS}
		exit
	fi

	sleep 1
	#rsync ${DOWNLOADDIR}/target/shell/little_feed.sh /home/watchdog
	#rsync python feed watchdog script to /home/watchdog
	if [ -d "${DOWNLOADDIR}/target/watchdog" ];then
		rsync -r ${DOWNLOADDIR}/target/watchdog/ /home/watchdog
	fi

	echo "move:${version}:0" > ${UPDATESTATUS}
}

move() {
	cd /root
	if [ ! -d "${DOWNLOADDIR}/target" ]
	then 
		echo "move file error!"
		echo "error:${version}:3" > ${UPDATESTATUS}
	else
		#删除只存在于/root中，不存在于更新包中的文件
		sleep 1

		#rsync shell script to /root
		if [ -d "${DOWNLOADDIR}/target/shell" ];then
			if [ -f "${DOWNLOADDIR}/target/shell/update_firmware.sh" ];then
				diff ${DOWNLOADDIR}/target/shell/update_firmware.sh /root/update_firmware.sh > /dev/null
				if [ $? -eq 1 ];then
					rsync ${DOWNLOADDIR}/target/shell/update_firmware.sh /root/update_firmware.sh
					exit
				fi
			fi		
			rsync -r ${DOWNLOADDIR}/target/shell/*.sh /root/
		fi
				
		#rsync python modules
		if [ -d "${DOWNLOADDIR}/target/python" ];then
			rsync -r ${DOWNLOADDIR}/target/python/*.so /usr/local/lib/python3.5/dist-packages/
		fi

		#rsync python run script to /root
		if [ -d "${DOWNLOADDIR}/target/run" ];then
			rsync -r ${DOWNLOADDIR}/target/run/*.py /root/
		fi

		#rsync image file to /root
		if [ -d "${DOWNLOADDIR}/target/image" ];then
			rsync -r ${DOWNLOADDIR}/target/image /root/
		fi

		#rsync image file to /root
		if [ -d "${DOWNLOADDIR}/target/ppp" ];then
			rsync -r ${DOWNLOADDIR}/target/ppp /etc/ppp/
		fi

		#config file rsync
		if [ ! -f "/root/net.conf" ];then
			cp ${DOWNLOADDIR}/target/net.conf /root
		fi

		if [ ! -f "/root/config.ini" ];then
			cp ${DOWNLOADDIR}/target/config.ini /root
		fi

		if [ -f "${DOWNLOADDIR}/target/ntp.conf " ];then
			rsync -r ${DOWNLOADDIR}/target/ntp.conf /etc/
		fi

		#crtfile rsync
		if [ -f "${DOWNLOADDIR}/target/mqtt.iotwonderful.cn.crt" ];then
			mkdir -p /root/crtfile
			rsync -r ${DOWNLOADDIR}/target/mqtt.iotwonderful.cn.crt /root/crtfile/
		fi

		if [ ! -d "/root/log" ];then
			mkdir -p /root/log
		fi

		#install frpc service
		if [ -d "${DOWNLOADDIR}/target/frp" ];then
			if [ -d "${DOWNLOADDIR}/target/frp/systemd" ];then
				rsync -r ${DOWNLOADDIR}/target/frp/systemd/* /lib/systemd/system/
			fi
			if [ -f "${DOWNLOADDIR}/target/frp/frpc" ];then
				rsync -r ${DOWNLOADDIR}/target/frp/frpc /usr/bin/
			fi
			if [ -f "${DOWNLOADDIR}/target/frp/frpc.ini" ];then
				rsync -r ${DOWNLOADDIR}/target/frp/frpc.ini /etc/frp/
			fi
		fi

		#ver=${FIRMWARE#*_}
		#ver=${ver%%.*}
		/root/set_config.sh "version " " ${version}"
		/root/set_config.sh "VERSION" "${version}"

		#rsync ${DOWNLOADDIR}/target/rc.local /etc/
		if [ -f "${DOWNLOADDIR}/systemd/zywldl.service" ];then
			rsync ${DOWNLOADDIR}/systemd/zywldl.service /lib/systemd/system/
			systemctl enable zywldl
		fi

		echo "clear:${version}:0" > ${UPDATESTATUS}
	fi
}

update_clear() {
	cd /root
	rm /home/download/*
	echo "done:${version}:0" > ${UPDATESTATUS}
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
