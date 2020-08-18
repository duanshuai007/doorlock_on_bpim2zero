#!/bin/sh

#	2020 07 16
#this script will generate a firmware
#
user=$(whoami)
if [ ${user} != "root" ]
then
	echo "only run this script in superuser!"
	exit
fi

if [ $# -lt 1 ]
then
	echo "please input version number!"
	exit
fi

version=$1

STONEFILE="python_modules/message_struct/message_struct.py"

if [ ! -f "${STONEFILE}" ]
then
	echo "STONE FILE IS NOT EXISTS"
	exit
fi

tarpassword=$(cat ${STONEFILE} | grep DOORSTONE | awk -F"=" '{print $2}')
if [ -z "${tarpassword}" ]
then
	print "can't find DOORSTONE in ${STONEFILE}"
	exit
fi

sourcedir=$(pwd)
target=${sourcedir}/target

if [ -d "${target}" ]
then
	rm -rf ${target}
fi

MD5FILE=${target}/md5file
BUILDFILE=${target}/buildfile


mkdir ${target}
mkdir -p ${target}/shell
mkdir -p ${target}/python
mkdir -p ${target}/image
mkdir -p ${target}/run
mkdir -p ${target}/systemd
mkdir -p ${target}/frp

cat /dev/null > ${MD5FILE}
cat /dev/null > ${BUILDFILE}

cd ${sourcedir}/python_modules
./make.sh build

for var in $(find . -name "*.so")
do
	newname=$(echo $var | awk -F"/" '{print $4}' | awk -F"." '{print $1}')
	mv ${var} ${target}/python/${newname}.so
	echo "python/${newname}.so:/usr/local/lib/python3.5/dist-packages/${newname}.so" >> ${BUILDFILE}
done


cd ${sourcedir}/shellscript

for var in $(find . -name "*")
do
	if [ -f "${var}" ];then 
		name=${var##*/}
		cp ${var} ${target}/shell/
		echo "shell/${name}:/root/${name}" >> ${BUILDFILE}
	fi
done

cd ${sourcedir}
#cp rc.local		${target}
cp config.ini	${target}
echo "config.ini:/root/config.ini" >> ${BUILDFILE}
cp crtfile/*	${target}
echo "mqtt.iotwonderful.cn.crt:/root/crtfile/mqtt.iotwonderful.cn.crt" >> ${BUILDFILE}

frpc_server_addr=$(cat frp/frpc.ini | grep server_addr | awk -F" = " '{print $2}')
frpc_server_port=$(cat frp/frpc.ini | grep server_port | awk -F" = " '{print $2}')
frpc_remote_addr=$(cat frp/frpc.ini | grep remote_port | awk -F" = " '{print $2}')

read -p "echo do you sure frpc_server_addr=${frpc_server_addr} frpc_server_port=${frpc_server_port} frpc_remote_addr=${frpc_remote_addr}?[Yy/Nn]: " yes 

if [ -n "${yes}" ]
then
	if [ "${yes}" == "N" -o "${yes}" == "n" ]
	then
		echo "please modify frp/frpc.ini"
		exit
	fi  
else
	echo "you must make your choice!"
	exit
fi

cp zywldl.service ${target}/systemd
echo "systemd/zywldl.service:/lib/systemd/system/zywldl.service" >> ${BUILDFILE}
cp zywlpppd.service ${target}/systemd
echo "systemd/zywlpppd.service:/lib/systemd/system/zywlpppd.service" >> ${BUILDFILE}
cp zywlmqtt.service ${target}/systemd
echo "systemd/zywlmqtt.service:/lib/systemd/system/zywlmqtt.service" >> ${BUILDFILE}
cp zywlwdt.service ${target}/systemd
echo "systemd/zywlwdt.service:/lib/systemd/system/zywlwdt.service" >> ${BUILDFILE}

cp frp/frpc.ini	${target}/frp
echo "frp/frpc.ini:/etc/frp/frpc.ini" >> ${BUILDFILE}
#cp net.conf ${target}
#echo "net.conf:/root/net.conf" >> ${BUILDFILE}
cp ntp.conf ${target}
echo "ntp.conf:/etc/ntp.conf" >> ${BUILDFILE}

cp image/error_160x160.png	${target}/image
echo "image/error_160x160.png:/root/image/error_160x160.png" >> ${BUILDFILE}
cp image/logo_160x160.png	${target}/image
echo "image/logo_160x160.png:/root/image/logo_160x160.png" >> ${BUILDFILE}
cp image/updateing_160x160.png ${target}/image
echo "image/updateing_160x160.png:/root/image/updateing_160x160.png" >> ${BUILDFILE}

mkdir -p ${target}/ppp
mkdir -p ${target}/ppp/mobile
mkdir -p ${target}/ppp/peers
mkdir -p ${target}/ppp/telecom
mkdir -p ${target}/ppp/unicom

cd ${sourcedir}/ppp
for var in $(find . -name "*")
do
	if [ -f "${var}" ];then
		path=${var%/*}
		path=${path#*/}
		filename=${var#*/}
		cp ${var} ${target}/ppp/${path}
		echo "ppp/${filename}:/etc/ppp/${filename}" >> ${BUILDFILE}
	fi
done

cd ${sourcedir}/pythonscript
for var in $(find . -name "*")
do
	if [ -f "${var}" ];then
		cp ${var} ${target}/run
		name=${var#*/}
		echo "run/${name}:/root/${name}" >> ${BUILDFILE}
	fi
done

cd ${target}
for var in $(find . -name "*")
do
	if [ -f ${var} ];then
		filename=${var#*/}
		if [ "${filename}" == "buildfile" -o "${filename}" == "md5file" ];then
			continue
		fi
		md5val=$(md5sum ${var} | awk -F" " '{print $1}')
		echo "${md5val} ${filename}" >> ${MD5FILE}
	fi
done
cd ${sourcedir}

wlan_enable=$(cat config.ini | grep -w wifi | awk -F" = " '{print $2}')
eth_enable=$(cat config.ini | grep -w eth | awk -F" = " '{print $2}')
sim_enable=$(cat config.ini | grep -w sim | awk -F" = " '{print $2}')
read -p "echo do you sure wlan:${wlan_enable} eth:${eth_enable} ppp=${sim_enable}?[Yy/Nn]: " yes 
if [ -n "${yes}" ]
then
	if [ "${yes}" == "N" -o "${yes}" == "n" ]
	then
		echo "please modify config.ini"
		exit
	fi  
else
	echo "you must make your choice!"
	exit
fi

if [ "${wlan_enable}" == "enable" ];then
	./set_current_wifi.sh choice eth0
elif [ "${eth_enable}" == "enable" ];then
	./set_current_wifi.sh choice wlan0
elif [ "${sim_enable}" == "enable" ];then
	./set_current_wifi.sh choice ppp0
else
	echo "至少要有一个可用的网络,请修改config.ini文件的对应选项"
	exit
fi

echo "compress password = ${tarpassword}"
tar -zcvf - target | openssl des3 -salt -k ${tarpassword} | dd of=firmware_${version}.des3.tar.gz

