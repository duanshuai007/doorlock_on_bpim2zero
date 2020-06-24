#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>

static char buf[256] = {1};
#define LCD_DRV_MAGIC               'K'
#define LCD_CMD_MAKE(cmd)           (_IO(LCD_DRV_MAGIC, cmd))
#define LCD_OPEN_SCREEN				6
#define LCD_CLOSE_SCREEN			7

static buffer[160 * 160];

int main(int argc,char *argv[])
{
	int fd = open("/dev/spilcd",O_RDWR);
	int ret;
	int pinstate;

	if(fd < 0)
	{
		perror("Open file failed!!!\r\n");
		return -1;
	}
	while(1){
#if 0
		ret = write(fd,"on",2);
		if(ret < 0){
			perror("Failed to write!!");
		}
		ret = read(fd, &pinstate, 1);

		sleep(1);

		ret = write(fd,"off",3);
		if(ret < 0){
			perror("Failed to write!!");
		}
		ret = read(fd, &pinstate, 1);

		sleep(1);
#else
		ioctl(fd, LCD_CMD_MAKE(LCD_CLOSE_SCREEN), 0);
		//sleep(1);
		//ioctl(fd, LCD_CMD_MAKE(2), 0);
		sleep(5);
		ioctl(fd, LCD_CMD_MAKE(LCD_OPEN_SCREEN), 0);
		sleep(5);
#endif
	}
	close(fd);
	return 0;
}
