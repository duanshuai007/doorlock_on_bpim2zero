

testfunc() {
	if [ $1 -eq 0 ]
	then
		echo "eth0"
		return
	fi
	if [ $1 -eq 1 ]
	then
		echo "wlan0"
		return
	fi
	if [ $1 -eq 2 ]
	then
		echo "ppp0"
		return
	fi
}

s=$(testfunc 2)
echo $s
