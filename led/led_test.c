#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <linux/ioctl.h>

#define TYPE 'D'

int main(int argc, char *argv[])
{
    int fd, ret;
    printf("main---\r\n");
    fd = open("/dev/s5p4418-led", O_RDONLY);
    if(fd < 0)
    {
        printf("open led error\r\n");
        exit(1);
    }
    //freq = atoi(argv[1]);
    //printf("freq:%d\r\n", freq);
    //ret = ioctl(fd, _IOWR(TYPE,,int), freq);
    while(1)
    {
        ret = ioctl(fd, _IOWR(TYPE,0,int), 0);
        sleep(1);
        ret = ioctl(fd, _IOWR(TYPE,1,int), 0);
        sleep(1);
    }
    return 0;
}
