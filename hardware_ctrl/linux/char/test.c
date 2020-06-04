#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
static char buf[256] = {1};
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
		//printf("Please input <on> or <off>:\n");
		//scanf("%s",buf);
		//if(strlen(buf) > 3){
		//	printf("Ivalid input!\n");
		//}
		//else
		//{
			ret = write(fd,"on",2);
			if(ret < 0){
				perror("Failed to write!!");
			}
			ret = read(fd, &pinstate, 1);
			//printf("pin=%d\n", pinstate);
				
			sleep(1);

			ret = write(fd,"off",3);
			if(ret < 0){
				perror("Failed to write!!");
			}
			ret = read(fd, &pinstate, 1);
			//printf("pin=%d\n", pinstate);
			sleep(1);
		//}
	}
	close(fd);
	return 0;
}
