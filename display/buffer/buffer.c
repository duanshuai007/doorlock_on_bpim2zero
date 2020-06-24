#include <stdio.h>
#include <stdlib.h>
#include <error.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <stdbool.h>
#include "Python.h"

#define LCD_DRV_MAGIC               'K'
#define LCD_CMD_MAKE(cmd)           (_IO(LCD_DRV_MAGIC, cmd))
#define LCD_WINDOW_START		3
#define LCD_WINDOW_CONTINUE		4
#define LCD_WINDOW_END			5
#define LCD_RESET				99

//160行每行162列
//每个点阵用4bit表示，0xf 或 0x0
//所以表示一列的数组大小就是162 / 2
//static unsigned char display_buffer[160 * 81];

#define  DEBUG	1

static int fd = -1;
volatile static bool inuse = false;

static PyObject * spilcd_on(PyObject *self,PyObject *args)
{
	if (fd < 0) {
#if DEBUG
		fd = 32;
#else
		fd = open("/dev/spilcd",O_RDWR);
		if(fd < 0) {   
			//PyErr_SetString(PyExc_TypeError, "can't open /dev/spilcd.");
			return Py_False;
		}
#endif
		return Py_True;
	} else {
		//PyErr_SetString(PyExc_TypeError, "/dev/spilcd already open.");
		return Py_True;
	}
}

static PyObject * spilcd_off(PyObject *self,PyObject *args)
{
	if (fd < 0) {
		//PyErr_SetString(PyExc_TypeError, "/dev/spilcd not open.");
		return Py_True;
	} else {
#if DEBUG
#else
		close(fd);
#endif
		fd = -1;
		return Py_True;
	}
}

/*
 *		输入参数为1维list
 *		LCD屏幕每行有160个像素点
 *		每个像素点用4bit来表示
 *		每行的寻址范围是0-162，其中超出160的点位不显示在屏幕上，但是在内存中必须要有占位
 */
static PyObject * spilcd_show(PyObject *self,PyObject *args)
{
	//if (inuse == true)
	//	return Py_False;
	inuse = true;
	//printf("===> enter spilcd\n");
	int i, j;
	PyObject *ret = Py_True;
	PyObject *f = NULL;
	PyObject *line = NULL;
	PyObject *point = NULL;

	Py_ssize_t num;
	Py_ssize_t pos = 0;
	unsigned char  val;
	unsigned char *display_buffer = NULL;

	unsigned char *test = (unsigned char *)malloc(1024);

	if (fd < 0) {
		return Py_False;
	}

	display_buffer = (unsigned char *)PyMem_Malloc(160 * 81);
	if (display_buffer == NULL) {
		return Py_False;
	}
	memset(display_buffer, 0, 160*81);
#if 1
	if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &f)) {
		return Py_False;
	}   
	printf("f->ob_refcnt = %d\n", f->ob_refcnt);
	num = PyList_Size(f);
	printf("num=%d\n", num);
	for(i = 0; i < num; i++) {
		pos = 0;
		line = PyList_GetItem(f, i);
		//printf("line->ob_refcnt = %d\n", line->ob_refcnt);
#if 1
		for (j = 0; j < num; j++) {
			point = PyList_GetItem(line, j);
			//printf("point->ob_refcnt = %d\n", point->ob_refcnt);
			val = (unsigned char)PyLong_AsLong(point);
			if ((j!=0) && (j%2 == 0))
				pos++;

			if (j%2 != 0)
				display_buffer[i*81 + pos] |= val;
			else
				display_buffer[i*81 + pos] |= (val << 4);					
		}
#endif
		//printf("line->ob_refcnt = %d\n", line->ob_refcnt);
	}
#endif
#if DEBUG
	
	for (i = 0; i < 160; i++) {
		for (j = 0; j < 81; j++) {
			printf("%02x", display_buffer[i*81 +j]);
		}
		printf("\n");
	}
#else
	ioctl(fd, LCD_CMD_MAKE(LCD_WINDOW_START), 162); 
	for (i = 0; i < 80; i++) {
		if ( ioctl(fd, LCD_CMD_MAKE(LCD_WINDOW_CONTINUE), &display_buffer[i * 162]) < 0) {
			PyErr_SetString(PyExc_TypeError, "spilcd ioctl error.");
			ret = Py_False;
			break;	
		}
	}   

	ioctl(fd, LCD_CMD_MAKE(LCD_WINDOW_END), 0);
#endif

	PyMem_Free(display_buffer);
	inuse = false;
	//printf("===> exit spilcd\n");
	return ret;
}

static PyMethodDef spilcd_methods[] = {
	{"show", spilcd_show, METH_VARARGS},
	{"on", spilcd_on, METH_VARARGS},
	{"off", spilcd_off, METH_VARARGS}
};

static struct PyModuleDef spilcdPyDem = {
	PyModuleDef_HEAD_INIT,
	"spilcd",
	"",
	-1,
	spilcd_methods
};

PyMODINIT_FUNC PyInit_spilcd(void)
{
	return PyModule_Create(&spilcdPyDem);
}
