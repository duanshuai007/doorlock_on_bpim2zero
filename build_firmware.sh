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
#tarpassword=$2

STONEFILE="python_modules/message_struct/message_struct.py"

if [ ! -f "${STONEFILE}" ]
then
	echo "STONE FILE IS NOT EXISTS"
	exit
fi

tarpassword=$(cat ${STONEFILE} | grep DOORSTONE | awk -F"=" '{print $2}')
if [ -z "${tarpassword}" ]
then
	print "can find DOORSTONE in ${STONEFILE}"
	exit
fi

target="./target"

if [ -d "${target}" ]
then
	rm -rf ${target}
fi

mkdir ${target}
mkdir -p ${target}/shell
mkdir -p ${target}/python
mkdir -p ${target}/image
mkdir -p ${target}/run
mkdir -p ${target}/systemd

cd ./python_modules
./make.sh build

for var in $(find . -name "*.so")
do
	newname=$(echo $var | awk -F"/" '{print $4}' | awk -F"." '{print $1}')
	mv ${var} ../${target}/python/${newname}.so
done

cd ..

cp shellscript/* ${target}/shell/

cp rc.local		${target}
cp config.ini	${target}
cp crtfile/*	${target}

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
cp -r frp	${target}
cp net.conf ${target}
cp ntp.conf ${target}

cp image/error_160x160.png	${target}/image
cp image/logo_160x160.png	${target}/image
cp image/update_160x160.jpg ${target}/image

cp -r ppp ${target}
cp pythonscript/* ${target}/run
cp -r watchdog ${target}

echo "compress password = ${tarpassword}"
tar -zcvf - ${target} | openssl des3 -salt -k ${tarpassword} | dd of=firmware_${version}.des3.tar.gz

