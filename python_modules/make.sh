tar=$1

export CROSS_COMPILE=arm-linux-gnueabihf-
export CC="${CROSS_COMPILE}gcc -pthread" 
export LDSHARED="${CC} -shared"
#export LDFLAGS="-L$(pwd)/armlib/python3.5m"

case $1 in
	"build")
	python3 setup.py build
	;;
	"install")
	python3 setup.py install --prefix=$(pwd)
	;;
	*)
	;;
esac
