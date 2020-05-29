obj-m	:=led-device.o led-driver.o 
CC		:=arm-none-linux-gnueabi-gcc
KDIR	:=/home/duanshuai/kernel/kernel
PWD		:=$(shell pwd)
all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules
clean:
	rm *.o *.order *.mod.c *.symvers led_d*.ko
