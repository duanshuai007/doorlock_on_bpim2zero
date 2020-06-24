#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <stdbool.h>
#include "Python.h"

static int fd = -1;
static unsigned char food = 0;
ssize_t eaten;

static PyObject * watchdog_open(PyObject *self,PyObject *args)
{
	if (fd < 0) {
		fd = open("/dev/watchdog",O_RDWR);
		if(fd < 0) {   
			//PyErr_SetString(PyExc_TypeError, "can't open /dev/spilcd.");
			Py_RETURN_FALSE;
		}
	}
	
	Py_RETURN_TRUE;
}

/*
 *		输入参数为1维list
 *		LCD屏幕每行有160个像素点
 *		每个像素点用4bit来表示
 *		每行的寻址范围是0-162，其中超出160的点位不显示在屏幕上，但是在内存中必须要有占位
 */
static PyObject * watchdog_feed(PyObject *self,PyObject *args)
{
	if (fd < 0)
		Py_RETURN_FALSE;

	eaten = write(fd, &food, 1);
	//printf("eaten=%d food=%d\n", eaten, food);
	Py_RETURN_TRUE;
}

static PyMethodDef watchdog_methods[] = {
	{"feed", watchdog_feed, METH_VARARGS},
	{"open", watchdog_open, METH_VARARGS},
};

static struct PyModuleDef watchdogPyDem = {
	PyModuleDef_HEAD_INIT,
	"watchdog",
	"",
	-1,
	watchdog_methods
};

PyMODINIT_FUNC PyInit_watchdog(void)
{
	return PyModule_Create(&watchdogPyDem);
}
