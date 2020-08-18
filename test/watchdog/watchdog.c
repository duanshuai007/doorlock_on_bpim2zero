#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <stdbool.h>
#include <linux/watchdog.h>
#include "Python.h"

static PyObject * watchdog_set_timeout(PyObject *self,PyObject *args)
{
	int fd;
	int val= 45;
	PyObject *value = NULL;

	fd = open("/dev/watchdog", O_RDWR);
	if (fd < 0)
		Py_RETURN_FALSE;

	if (!PyArg_ParseTuple(args, "O",  &value)) {
		Py_RETURN_FALSE;
	}

	//val = (int)PyLong_AsLong(value);

	if (ioctl(fd, WDIOC_SETTIMEOUT, &val) != 0) {
		printf("set watchdog timeout error!\n");
		close(fd);
		Py_RETURN_FALSE;
	}
	printf("set watchdog timeout:%d\n", val);

	close(fd);
	Py_RETURN_TRUE;
}

static PyObject * watchdog_get_timeout(PyObject *self,PyObject *args)
{
	int fd;
	int val;

	fd = open("/dev/watchdog", O_RDWR);
	if (fd < 0)
		Py_RETURN_FALSE;

	if (ioctl(fd, WDIOC_GETTIMEOUT, &val) != 0) {
		printf("get watchdog timeout error\n");
		close(fd);
		Py_RETURN_FALSE;
	}
	printf("get watchdog timeout:%d\n", val);

	close(fd);
	//return PyLong_FromLong(val);
	return Py_BuildValue("i", val);
}

static PyObject * watchdog_feed(PyObject *self,PyObject *args)
{
	int fd = -1;

	fd = open("/dev/watchdog",O_RDWR);
	if (fd < 0)
		Py_RETURN_FALSE;

	//write(fd, "w", 1);
	ioctl(fd, WDIOC_KEEPALIVE, 0);
	printf("keepalive watchdog\n");

	close(fd);
	Py_RETURN_TRUE;
}

static PyObject * watchdog_stop(PyObject *self,PyObject *args)
{
	int fd = -1;

	fd = open("/dev/watchdog",O_RDWR);
	if (fd < 0)
		Py_RETURN_FALSE;

	write(fd, "V", 1);

	close(fd);
	Py_RETURN_TRUE;
}

static PyObject * watchdog_get_bootstatus(PyObject *self,PyObject *args)
{
	int fd = -1;
	int bootstatus;

	fd = open("/dev/watchdog",O_RDWR);
	if (fd < 0)
		Py_RETURN_FALSE;

	if (ioctl(fd, WDIOC_GETBOOTSTATUS, &bootstatus) == 0) {
		printf("last boot is caused by: %s \n", (bootstatus != 0) ? "watchdog" : "power_on_reset");
	} else {
		printf("error:cannot read watchdog status\n");
	}

	close(fd);
	//return PyLong_FromLong(bootstatus);
	return Py_BuildValue("i", bootstatus);
}

static PyMethodDef watchdog_methods[] = {
	{"set_timeout", watchdog_set_timeout, METH_VARARGS},
	{"get_timeout", watchdog_get_timeout, METH_VARARGS},
	{"feed", watchdog_feed, METH_VARARGS},
	{"get_bootstatus", watchdog_get_bootstatus, METH_VARARGS},
	{"stop", watchdog_stop, METH_VARARGS},
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
