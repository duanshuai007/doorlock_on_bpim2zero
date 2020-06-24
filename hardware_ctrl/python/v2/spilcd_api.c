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
#include "Python.h"

#define  DEBUG	1

#define GPIOA_BASE	0x01C20000
#define OFFSET		0x0800
#define GPIO_SIZE	0x1000

volatile uint32_t *gpio_map = NULL;
static int mem_fd = -1;

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

volatile gpio_t *GPIO_PTR[6];

typedef struct spilcd_pin_t {
	uint8_t sda;
	uint8_t sck;
	uint8_t rst;
	uint8_t cs;
	uint8_t a0;
} spilcd_pin_t;

spilcd_pin_t spilcd_pin;

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
	//printf("set pin[%d] to %d\n", pin, val);
	//printf("oldvalue=%08x\n", oval);
	if (val)
		oval |= 1 << pin;	
	else 
		oval &= ~(1 << pin);
	GPIO_PTR[chip]->dat = oval;
	//oval = 0;
	//oval = GPIO_PTR[chip]->dat;
	//printf("newvalue=%08x\n", oval);
}

static PyObject * spilcd_open(PyObject *self, PyObject *args)
{
	int i;

	printf("spilcd_open\n");
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
		GPIO_PTR[i] = (volatile gpio_t *)(gpio_map + ((OFFSET + 0x24 * i) >> 2));
	}

	spilcd_pin.sda = 15;
	spilcd_pin.sck = 14;
	spilcd_pin.rst = 16;
	spilcd_pin.a0 = 21;
	spilcd_pin.cs = 13;
	gpio_set_func(GPIOA, 15, FUNC_OUTPUT);
	gpio_set_func(GPIOA, 14, FUNC_OUTPUT);
	gpio_set_func(GPIOA, 16, FUNC_OUTPUT);
	gpio_set_func(GPIOA, 21, FUNC_OUTPUT);
	gpio_set_func(GPIOA, 13, FUNC_OUTPUT);
	gpio_set_func(GPIOA, 12, FUNC_OUTPUT);
	
	gpio_set_value(GPIOA, spilcd_pin.sda, 1);
	gpio_set_value(GPIOA, spilcd_pin.sck, 1);
	gpio_set_value(GPIOA, spilcd_pin.cs, 1);
	gpio_set_value(GPIOA, spilcd_pin.a0, 1);
	gpio_set_value(GPIOA, spilcd_pin.rst, 1);
	printf("spilcd_open end\n");

	Py_RETURN_TRUE;
}

static PyObject * spilcd_close(PyObject *self,PyObject *args)
{
	gpio_set_func(GPIOA, spilcd_pin.sda, FUNC_DISABLE);
	gpio_set_func(GPIOA, spilcd_pin.sck, FUNC_DISABLE);
	gpio_set_func(GPIOA, spilcd_pin.rst, FUNC_DISABLE);
	gpio_set_func(GPIOA, spilcd_pin.cs, FUNC_DISABLE);
	gpio_set_func(GPIOA, spilcd_pin.a0, FUNC_DISABLE);
	munmap((void *)gpio_map, GPIO_SIZE);
	close(mem_fd);
	Py_RETURN_TRUE;
}

static PyObject * spilcd_set_doorlock_open(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, 12, 0);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_doorlock_close(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, 12, 1);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_sda_high(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.sda, 1);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_sda_low(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.sda, 0);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_sck_high(PyObject *self,PyObject *args) {	
	gpio_set_value(GPIOA, spilcd_pin.sck, 1);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_sck_low(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.sck, 0);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_cs_high(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.cs, 1);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_cs_low(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.cs, 0);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_a0_high(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.a0, 1);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_a0_low(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.a0, 0);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_rst_high(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.rst, 1);
	Py_RETURN_NONE;
}
static PyObject * spilcd_set_rst_low(PyObject *self,PyObject *args) {
	gpio_set_value(GPIOA, spilcd_pin.rst, 0);
	Py_RETURN_NONE;
}

static PyMethodDef spilcd_methods[] = {
	{"on", spilcd_open, METH_VARARGS},
	{"off", spilcd_close, METH_VARARGS},
	{"set_doorlock_open", spilcd_set_doorlock_open, METH_VARARGS},
	{"set_doorlock_close", spilcd_set_doorlock_close, METH_VARARGS},
	{"set_sda_high", spilcd_set_sda_high, METH_VARARGS},
	{"set_sda_low", spilcd_set_sda_low, METH_VARARGS},
	{"set_sck_high", spilcd_set_sck_high, METH_VARARGS},
	{"set_sck_low", spilcd_set_sck_low, METH_VARARGS},
	{"set_cs_high", spilcd_set_cs_high, METH_VARARGS},
	{"set_cs_low", spilcd_set_cs_low, METH_VARARGS},
	{"set_a0_high", spilcd_set_a0_high, METH_VARARGS},
	{"set_a0_low", spilcd_set_a0_low, METH_VARARGS},
	{"set_rst_high", spilcd_set_rst_high, METH_VARARGS},
	{"set_rst_low", spilcd_set_rst_low, METH_VARARGS},
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

	/*if (Py_AtExit(cleanup) != 0) {
		
	}*/
	return module;
}
