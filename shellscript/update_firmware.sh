#!/bin/bash

#update firmware
DOWNLOADDIR="/home/firmware"
UPDATESTATUS="/home/ubuntu/update_status"
BACKUPDIR="/home/backfile"

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
	sync
	exit
fi

cat /dev/null > /home/ubuntu/updatelog

all_file_backup() {
	mkdir -p ${BACKUPDIR}
	mkdir -p ${BACKUPDIR}/python
	mkdir -p ${BACKUPDIR}/script
	mkdir -p ${BACKUPDIR}/systemd
	mkdir -p ${BACKUPDIR}/frp

	#LoggingQueue.so checkfiletype.so config.so downloadfile.so generate_pillow_buffer.so message_struct.so mqtt.so spilcd_api.so uncompressfirmware.so
	#watchdog.so wx2vcode.so
	cp /usr/local/lib/python3.5/dist-packages/LoggingQueue.so	${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/checkfiletype.so	${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/config.so			${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/downloadfile.so	${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/generate_pillow_buffer.so		${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/message_struct.so	${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/mqtt.so			${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/spilcd_api.so		${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/uncompressfirmware.so		${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/watchdog.so		${BACKUPDIR}/python
	cp /usr/local/lib/python3.5/dist-packages/wx2vcode.so		${BACKUPDIR}/python

	cp -r /root/* ${BACKUPDIR}/script
	cp /lib/systemd/system/zywl* ${BACKUPDIR}/systemd
	cp /etc/frp/frpc.ini ${BACKUPDIR}/frp
}

resume_all_file() {
	cp ${BACKUPDIR}/python/* /usr/local/lib/python3.5/dist-packages/
	cp -r ${BACKUPDIR}/script/* /root/
	cp ${BACKUPDIR}/systemd/* /lib/systemd/system/
	cp ${BACKUPDIR}/frp/* /etc/frp/
}

tarfile() {
	python3 /root/showimage.py update
	if [ -d "${DOWNLOADDIR}.back" ]
	then 
		rm -rf "${DOWNLOADDIR}.back"
	fi

	if [ -d "${DOWNLOADDIR}" ]
	then
		mv ${DOWNLOADDIR} ${DOWNLOADDIR}.back
	fi

	mkdir -p ${DOWNLOADDIR}

	all_file_backup

	#该文件必须首先要存在/root目录下才能解压
	python3 /root/uncompress.py ${FIRMWARE} ${DOWNLOADDIR}
	if [ ! -d "${DOWNLOADDIR}/target" ]
	then
		echo "tar firmware:${FIRMWARE} failed"
		echo "error:${version}:2" > ${UPDATESTATUS}
		sync
		exit
	fi

	sleep 1
	if [ -d "${DOWNLOADDIR}/target/watchdog" ];then
		cp -r ${DOWNLOADDIR}/target/watchdog/ /home/watchdog
	fi

	firmwaredir="${DOWNLOADDIR}/target"
	for var in $(cat ${firmwaredir}/md5file | awk -F" " '{print $2}')
	do
		oldmd5val=$(cat ${firmwaredir}/md5file | grep "${var}" | awk -F" " '{print $1}')
		newmd5val=$(md5sum ${firmwaredir}/${var} | awk -F" " '{print $1}')
		echo "file:${var} old:${oldmd5val} new:${newmd5val}" >> /home/ubuntu/updatelog
		if [ "${oldmd5val}" != "${newmd5val}" ];then
			echo "error:${version}:4" > ${UPDATESTATUS}
			sync
			exit
		fi
	done

	echo "move:${version}:0" > ${UPDATESTATUS}
	sync
}

move() {
	cd /root
	if [ ! -d "${DOWNLOADDIR}/target" ]
	then 
		echo "move file error!"
		echo "error:${version}:3" > ${UPDATESTATUS}
		sync
	else
		if [ -d "${DOWNLOADDIR}/target/shell" ];then
			if [ -f "${DOWNLOADDIR}/target/shell/update_firmware.sh" ];then
				diff ${DOWNLOADDIR}/target/shell/update_firmware.sh /root/update_firmware.sh > /dev/null
				if [ $? -eq 1 ];then
					cp ${DOWNLOADDIR}/target/shell/update_firmware.sh /root/update_firmware.sh
					exit
				fi
			fi		
		fi

		prefix=${DOWNLOADDIR}/target
		if [ ! -f "${prefix}/buildfile" ];then
			echo "error:${version}:6" > ${UPDATESTATUS}
			sync
			exit
		fi

		for var in $(cat ${prefix}/buildfile)
		do
			src=$(echo ${var} | awk -F":" '{print $1}')
			dst=$(echo ${var} | awk -F":" '{print $2}')
			cp ${prefix}/${src} ${dst}
		done
		
		echo "clear:${version}:0" > ${UPDATESTATUS}
		sync
	fi
}

update_clear() {
	cd /root
	rm /home/download/*

	errornumber=0
	echo "==================" >> /home/ubuntu/updatelog

	prefix=${DOWNLOADDIR}/target
	for var in $(cat ${prefix}/buildfile)
	do
		src=$(echo ${var} | awk -F":" '{print $1}')
		dst=$(echo ${var} | awk -F":" '{print $2}')
		
		after=$(md5sum ${dst} | awk -F" " '{print $1}')
		before=$(cat ${prefix}/md5file | grep "${src}" | awk -F" " '{print $1}')
		echo "file:${src} after:${after} before:${before}" >> /home/ubuntu/updatelog
		if [ "${after}" != "${before}" ];then
			errornumber=1
		fi
	done

	if [ ${errornumber} -ne 0 ];then
		resume_all_file
		echo "error:${version}:5" > ${UPDATESTATUS}
		sync
		exit
	fi

	if [ ! -f /usr/bin/zywldl ];then
		ln -s /root/watch.sh /usr/bin/zywlmqtt
	fi
	if [ ! -f /usr/bin/zywlpppd ];then
		ln -s /root/watchpppd.sh /usr/bin/zywlmqtt
	fi
	if [ ! -f /usr/bin/zywlmqtt ];then
		ln -s /root/watchmqtt.sh /usr/bin/zywlmqtt
	fi

	/root/set_config.sh "version " " ${version}"
	/root/set_config.sh "VERSION" "${version}"

	echo "done:${version}:0" > ${UPDATESTATUS}
	sync
}

if [ -n "${sta}" ]
then
	case ${sta} in 
	"start")
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
