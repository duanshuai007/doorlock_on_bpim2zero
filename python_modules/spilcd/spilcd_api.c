#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <error.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <stdbool.h>
#include <sys/mman.h>
#include <string.h>
#include <errno.h>
#include <time.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <semaphore.h>
#include "Python.h"

#define GPIOA_BASE	0x01C20000
#define OFFSET		0x0800
#define GPIO_SIZE	0x1000

#define GPIOA	0
#define GPIOC	1
#define GPIOD	2
#define GPIOE	3
#define GPIOF	4
#define GPIOG	5
#define FUNC_INPUT	0
#define FUNC_OUTPUT	1
#define FUNC_DISABLE	0x7

#define CS_ENABLE   0
#define CS_DISABLE  1
#define A0_CMD      0
#define A0_DATA     1
#define RST_ENABLE  0
#define RST_DISABLE 1

typedef struct gpio_t {
	volatile uint32_t cfg[4];
	volatile uint32_t dat;
	volatile uint32_t drv[2];
	volatile uint32_t pul[2];
} gpio_t;


typedef struct spilcd_pin_t {
	uint8_t sda;
	uint8_t sck;
	uint8_t rst;
	uint8_t cs;
	uint8_t a0;
} spilcd_pin_t;

volatile uint32_t *gpio_map = NULL;
static int mem_fd = -1;
spilcd_pin_t spilcd_pin;
static gpio_t *GPIO_PTR[6];
static unsigned char disp_buffer[160 * 81];
static sem_t sem_as_open;
static sem_t sem_write;

int c_sleep_msec(long milliseconds) {
	struct timespec req;
	//struct timespec rem;
	if(milliseconds > 999) {
		req.tv_sec = (int)(milliseconds / 1000);  /* Must be Non-Negative */
		req.tv_nsec = (milliseconds - ((long)req.tv_sec * 1000)) * 1000000; /* Must be in range of 0 to 999999999 */
	}
	else {
		req.tv_sec = 0;                         /* Must be Non-Negative */
		req.tv_nsec = milliseconds * 1000000;    /* Must be in range of 0 to 999999999 */
	}
	//rem = NULL;
	return nanosleep(&req , NULL);
}

int c_sleep_nsec(long nanoseconds) {
	struct timespec req;
	//struct timespec rem;
	if (nanoseconds > 999999999) {
		req.tv_sec = (int)(nanoseconds / 1000000000);
		req.tv_nsec = (nanoseconds - ((long)req.tv_sec * 1000000000));
	}
	else {
		req.tv_sec = 0;
		req.tv_nsec = nanoseconds;
	}
	//rem = NULL;
	return nanosleep(&req , NULL);
}

static void gpio_set_func(uint32_t chip, uint32_t pin, uint32_t func)
{
	uint32_t cfg_offset = pin / 8;
	uint32_t pin_offset = pin % 8;
	uint32_t val;
	
	val = GPIO_PTR[chip]->cfg[cfg_offset];
	val &= ~(0x7 << (4 * pin_offset));
	val |= (func << (4 * pin_offset));
	GPIO_PTR[chip]->cfg[cfg_offset] = val;
}

static void gpio_set_value(uint8_t chip, uint8_t pin, uint8_t val)
{
	uint32_t oval;
	oval = GPIO_PTR[chip]->dat;
	if (val)
		oval |= 1 << pin;	
	else 
		oval &= ~(1 << pin);
	GPIO_PTR[chip]->dat = oval;
}

static void begin_write_data(void)
{
	gpio_set_value(GPIOA, spilcd_pin.rst, RST_DISABLE);
	gpio_set_value(GPIOA, spilcd_pin.cs, CS_ENABLE);
	gpio_set_value(GPIOA, spilcd_pin.a0, A0_DATA);
	c_sleep_nsec(200);
}

static void continue_write_data(unsigned char dat)
{
	int i;

	for (i = 0; i < 8; i++) {
		gpio_set_value(GPIOA, spilcd_pin.sck, 0);
		if ((dat & 0x80) == 0)
			gpio_set_value(GPIOA, spilcd_pin.sda, 0);
		else
			gpio_set_value(GPIOA, spilcd_pin.sda, 1);
		//c_sleep_nsec(5);
		gpio_set_value(GPIOA, spilcd_pin.sck, 1);
		dat <<= 1;
		//c_sleep_nsec(5);
	}
}

static void end_write_data(void)
{
	gpio_set_value(GPIOA, spilcd_pin.cs, CS_DISABLE);
}

static void write_cmd(uint8_t cmd)
{
	int i;
	gpio_set_value(GPIOA, spilcd_pin.cs, CS_ENABLE);
	gpio_set_value(GPIOA, spilcd_pin.a0, A0_CMD);
	c_sleep_nsec(5);
	//printf("write cmd:%02x sda=%d sck=%d cs=%d a0=%d\n", cmd, spilcd_pin.sda, spilcd_pin.sck, spilcd_pin.cs, spilcd_pin.a0);
	for (i = 0; i < 8; i++) {
		gpio_set_value(GPIOA, spilcd_pin.sck, 0);
		if ((cmd & 0x80) == 0)
			gpio_set_value(GPIOA, spilcd_pin.sda, 0);
		else
			gpio_set_value(GPIOA, spilcd_pin.sda, 1);
		c_sleep_nsec(1);
		gpio_set_value(GPIOA, spilcd_pin.sck, 1);
		c_sleep_nsec(1);
		cmd <<= 1;
	}
	c_sleep_nsec(50);
	gpio_set_value(GPIOA, spilcd_pin.cs, CS_DISABLE);
}


static void lcd_window_init(unsigned char start_row, unsigned char start_col, unsigned char width, unsigned char height)
{
	if (start_row > 159 || (start_row + height > 160)) {
		return;
	}

	if (start_col > 54 || (start_col + width > 54)) {
		return;
	}

	write_cmd(0x05);//set column
	write_cmd(0x12);
	write_cmd(0x60);//set row 
	write_cmd(0x70);

	//设置窗口左边界
	write_cmd(0xf4);
	write_cmd(start_col + 37);
	//设置窗口上边界
	write_cmd(0xf5);
	write_cmd(start_row);
	//设置窗口右边界
	write_cmd(0xf6);
	write_cmd(start_col + 37 + width);
	//设置窗口下边界
	write_cmd(0xf7);
	write_cmd(start_row + height);
}

static void lcd_window_enable(bool state)
{
	if (state == true)
		write_cmd(0xf8 | 0);
	else
		write_cmd(0xf8 | 1);
}

static void lcd_init(void)
{   
	//系统初始化
	write_cmd(0xe2);
	c_sleep_msec(200);

	//设置温度补偿系数:00
	write_cmd(0x24 | 0);

	//电源控制设置
	//pc0:0->承受lcd负载<=13nF, 1->承受lcd负载为13nF<lcd<=22nF
	//pc1:0->关闭内置升压电路, 1->启用内部升压电路
	write_cmd(0x28 | 3);

	//lcd映像设置
	write_cmd(0xc0);

	//设置帧率 取值范围0-3
	write_cmd(0xa0 | 2);
	//M信号波形设置
	write_cmd(0xc8);
	write_cmd(0x0f);

	//显示数据格式设置
	//0: BRGBGRBGR...BGR
	//1: RGBRGBRGB...RGB
	write_cmd(0xd0 | 1);

	//RGB数据格式设置
	//增强模式为0(对应0xa8指令中的值), 
	//此处设置为1时: 数据格式:RRRR-GGGGG-BBB，每3个字节存储两组数据
	//R R R R G G G G 
	//G B B B R R R R
	//G G G G G B B B
	//此处设置为2时:数据格式:RRRRR-GGGGGG-BBBBB,可以直接保存在16位ram内
	//R R R R R G G G
	//G G G B B B B B
	write_cmd(0xd4 | 1);

	//偏压比设置 取值范围0-3
	write_cmd(0xe8 | 1);


	//设置对比度电压 取值范围0-255
	write_cmd(0x81);
	write_cmd(188);

	//设置全显示 0->关闭全显示 1->打开全显示
	//write_cmd(0xa4 | 0);

	//设置负性显示 0关闭 1开启
	//write_cmd(0xa6 | 0);

	//显示使能设置
	//(0): 1开显示 0关显示
	//(1): 1开启灰度显示 0关闭灰度显示
	//(2): 1关闭增强模式 0开启增强模式 
	write_cmd(0xa8 | (1<<0) | (0 << 1) | (0 << 2));
	//该指令执行后需要延时10毫秒不操作lcd模块来保证不对模块造成有害的干扰
	c_sleep_msec(20);
}

static PyObject * spilcd_open(PyObject *self, PyObject *args)
{
	int i;

	//非0表示已经打开
	if (sem_trywait(&sem_as_open))
		Py_RETURN_TRUE;

	if ((mem_fd = open("/dev/mem", O_RDWR|O_SYNC)) < 0) {
		printf("open /dev/mem faiiled\n");
		Py_RETURN_FALSE;
	}
	
	gpio_map = mmap(0, GPIO_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, mem_fd, GPIOA_BASE);
	if (gpio_map == MAP_FAILED) {
		printf("spilcd  mmap failed\n");
		printf("%s\n", strerror(errno));
		Py_RETURN_FALSE;
	}
	
	for (i = 0; i < 6; i++) {
		GPIO_PTR[i] = (gpio_t *)(gpio_map + ((OFFSET + 0x24 * i) >> 2));
	}

	spilcd_pin.sda = 15;
	spilcd_pin.sck = 14;
	spilcd_pin.rst = 16;
	spilcd_pin.a0 = 21;
	spilcd_pin.cs = 13;
	gpio_set_func(GPIOA, spilcd_pin.sda, FUNC_OUTPUT);
	gpio_set_func(GPIOA, spilcd_pin.sck, FUNC_OUTPUT);
	gpio_set_func(GPIOA, spilcd_pin.rst, FUNC_OUTPUT);
	gpio_set_func(GPIOA, spilcd_pin.cs, FUNC_OUTPUT);
	gpio_set_func(GPIOA, spilcd_pin.a0, FUNC_OUTPUT);

	gpio_set_func(GPIOA, 12, FUNC_OUTPUT);

	gpio_set_value(GPIOA, spilcd_pin.sda, 1);
	gpio_set_value(GPIOA, spilcd_pin.sck, 1);
	gpio_set_value(GPIOA, spilcd_pin.rst, 1);
	gpio_set_value(GPIOA, spilcd_pin.cs, 1);
	gpio_set_value(GPIOA, spilcd_pin.a0, 1);

	lcd_init();
	lcd_window_init( 0, 0, 53, 159);
	lcd_window_enable(true);
	
//	printf("spilcd_open end\n");

	Py_RETURN_TRUE;
}

static PyObject * spilcd_close(PyObject *self,PyObject *args)
{
	if (sem_trywait(&sem_as_open)) {
		lcd_window_enable(false);
		gpio_set_func(GPIOA, spilcd_pin.sda, FUNC_DISABLE);
		gpio_set_func(GPIOA, spilcd_pin.sck, FUNC_DISABLE);
		gpio_set_func(GPIOA, spilcd_pin.rst, FUNC_DISABLE);
		gpio_set_func(GPIOA, spilcd_pin.cs, FUNC_DISABLE);
		gpio_set_func(GPIOA, spilcd_pin.a0, FUNC_DISABLE);
		munmap((void *)gpio_map, GPIO_SIZE);
		close(mem_fd);
		sem_post(&sem_as_open);
	}
	Py_RETURN_TRUE;
}

static PyObject * spilcd_close_screen(PyObject *self,PyObject *args)
{
	if (!sem_trywait(&sem_write)) {
		write_cmd(0xa8 | (0 << 2) | (0 << 1) | (0 << 0));
		sem_post(&sem_write);
		Py_RETURN_TRUE;
	}
	Py_RETURN_FALSE;
}

static PyObject * spilcd_set_doorlock(PyObject *self,PyObject *args)
{
	PyObject *value = NULL;
	int val;

	if (!PyArg_ParseTuple(args, "O",  &value)) {
		Py_RETURN_FALSE;
	}

	val = (int)PyLong_AsLong(value);

	gpio_set_value(GPIOA, 12, val);
	Py_RETURN_TRUE;
}

static PyObject * spilcd_show(PyObject *self,PyObject *args)
{
	int i, j;
	PyObject *f = NULL;
	PyObject *line = NULL;
	PyObject *point = NULL;
	Py_ssize_t num;
	Py_ssize_t pos = 0;
	unsigned char  val;

	if (sem_trywait(&sem_write))
		Py_RETURN_FALSE;

	if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &f)) {
		sem_post(&sem_write);
		Py_RETURN_FALSE;
	}   
	//printf("spilcd show start\n");
//	printf("spilcd_api show f->ob_refcnt = %d\n", f->ob_refcnt);
	num = PyList_Size(f);
//	printf("num=%d\n", num);
	memset(disp_buffer, 0, sizeof(disp_buffer));

	for(i = 0; i < num; i++) {
		pos = 0;
		line = PyList_GetItem(f, i); 
		for (j = 0; j < num; j++) {
			point = PyList_GetItem(line, j); 
			//printf("point->ob_refcnt = %d\n", point->ob_refcnt);
			val = (unsigned char)PyLong_AsLong(point);
			if ((j!=0) && (j%2 == 0)) 
				pos++;

			if (j%2 != 0)
				disp_buffer[i*81 + pos] |= val;
			else
				disp_buffer[i*81 + pos] |= (val << 4);    
		} 
	}

	Py_DECREF(f);
/*
	for (i = 0; i < 160; i++) {
		for (j = 0; j < 81; j++) 
			printf("%02x", disp_buffer[i*81 +j]);
		printf("\n");
	}
*/
	//start write data to screen
	//enable display
	write_cmd(0xa8 | (0 << 2) | (0 << 1) | (1 << 0));
	c_sleep_msec(5);
	begin_write_data();
	for (i = 0; i < 160; i++) {
		for (j = 0; j < 81; j++) {
			continue_write_data(disp_buffer[i * 81 + j]);
		}
	}
	end_write_data();

	sem_post(&sem_write);
	//printf("spilcd show start\n");
	Py_RETURN_TRUE;
}

static PyMethodDef spilcd_methods[] = {
	{"on", spilcd_open, METH_VARARGS},
	{"off", spilcd_close, METH_VARARGS},
	{"close_screen", spilcd_close_screen, METH_VARARGS},
	{"show", spilcd_show, METH_VARARGS},
	{"set_doorlock", spilcd_set_doorlock, METH_VARARGS},
};

static struct PyModuleDef spilcdPyDem = {
	PyModuleDef_HEAD_INIT,
	"spilcd_api",
	"",
	-1,
	spilcd_methods
};

PyMODINIT_FUNC PyInit_spilcd_api(void)
{
	PyObject *module = NULL;
	module = PyModule_Create(&spilcdPyDem);
	
	if (!PyEval_ThreadsInitialized())
		PyEval_InitThreads();

	//第二个参数的意义时该信号量是进程间共享还是一个进程的多个线程间共享
	//0 = 一个进程的多个线程间共享
	//1 = 多个进程间共享
	//第三个参数是该信号量的初始值
	sem_init(&sem_as_open, 1, 1);
	sem_init(&sem_write, 1, 1);
	/*if (Py_AtExit(cleanup) != 0) {
		
	}*/
	return module;
}
