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

#define  DEBUG	0

/*
 *	输入参数为二维list
 */
#if 0
static PyObject * spilcd_display(PyObject *self,PyObject *args)
{
#if DEBUG
	int fd =32;
#else
	int fd = open("/dev/spilcd",O_RDWR);
#endif
	int i, j;
	PyObject *ret = NULL;
	PyObject *pList = NULL;
	PyObject *pCList = NULL;
	PyObject *pItem = NULL;
	Py_ssize_t nCList;
	Py_ssize_t nPoint;
	
	//两侧留白，上下留白
	//像素点大小
	int pointsize;
	int m,n;

	if(fd < 0) {   
		//printf("open /dev/spilcd failed\n");
		PyErr_SetString(PyExc_TypeError, "can't open /dev/spilcd.");
		ret = Py_BuildValue("s", "False");
		return ret;
	}   

	if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &pList)) {
		close(fd);
		PyErr_SetString(PyExc_TypeError, "parameter must be a list.");
		ret = Py_BuildValue("s", "False");
		return ret;
	}

	memset(display_buffer, 0, sizeof(display_buffer));
	nCList = PyList_Size(pList);
	//二维码横竖都是同样的长度,每个点的宽度最少为3,则最大行数应为160/3 = 53行
	if (nCList > 160 / 3) {
		close(fd);
		PyErr_SetString(PyExc_TypeError, "image map too big.");
		ret = Py_BuildValue("s", "False");
		return ret;
	}

	pointsize = 160 / nCList;

	for (i = 0; i < nCList; i++) {
		pCList = PyList_GetItem(pList, i);
		nPoint = PyList_Size(pCList);
		for (j = 0; j < nPoint; j++) {
			pItem = PyList_GetItem(pCList, j);
			//行列确定一个点的值，将该点绘画成一个方块，填充到buffer中
			//PyObject_Print(pItem, stdout, 0);
			if(PyObject_IsTrue(pItem)) {

				for (m = 0; m < pointsize; m++) {
					for (n = 0; n < pointsize; n++) {
						//计算该点在buffer中的位置
						int pos = ((i * pointsize) + m)*81 + ((j*pointsize + n)/2) + ((j*pointsize +n)%2);
						//计算该点在图像中列的位置
						int poss = j*pointsize + n;
						//printf("pos = %d, poss = %d\n", pos, poss);	
						if (poss % 2 != 0) {
							pos -= 1;
							display_buffer[pos] |= 0x0f;
						} else {
							display_buffer[pos] |= 0xf0;
						}
					}
				}
			}
		}
	}

#if DEBUG
	for (i = 0; i < 160; i++) {
		for (j = 0; j < 81; j++) {
			//printf("%d", display_buffer[(i)*162 + j]>0?1:0);
			printf("%02x", display_buffer[i*81 +j]);
		}
		printf("\n");
	}
#endif
	ioctl(fd, LCD_CMD_MAKE(LCD_WINDOW_START), 162); 
	for (i = 0; i < 80; i++) {
		//设置显示的行
		//设置行的内容
		ioctl(fd, LCD_CMD_MAKE(LCD_WINDOW_CONTINUE), &display_buffer[i * 162]);
		sleep(0.01);
	}

	close(fd);
	ret = Py_BuildValue("s", "True");

	return ret;
}
#endif
static int fd = -1;

static PyObject * spilcd_on(PyObject *self,PyObject *args)
{
	if (fd < 0) {
		fd = open("/dev/spilcd",O_RDWR);
		if(fd < 0) {   
			PyErr_SetString(PyExc_TypeError, "can't open /dev/spilcd.");
			return Py_False;
		}
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
		close(fd);
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
	int i, j;
	PyObject *ret = Py_True;
	PyObject *pList = NULL;
	PyObject *pListItem = NULL;
	PyObject *pItem = NULL;
	Py_ssize_t nCList = 0;
	int pos = 0;
	unsigned char  val;
	unsigned char *display_buffer = NULL;
	
	/*
	int fd = open("/dev/spilcd",O_RDWR);
	if(fd < 0) {   
		PyErr_SetString(PyExc_TypeError, "can't open /dev/spilcd.");
		return Py_False;
	}   
	*/

	if (fd < 0) {
		PyErr_SetString(PyExc_TypeError, "must first call spilcd.on.");
		return Py_False;
	}

	if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &pList)) {
		close(fd);
		PyErr_SetString(PyExc_TypeError, "parameter must be a list.");
		return Py_False;
	}

	nCList = PyList_Size(pList);

	display_buffer = (unsigned char *)PyMem_Malloc(160 * 81);
	if (display_buffer == NULL) {
		PyErr_SetString(PyExc_TypeError, "PyMem_Malloc failed.");
		return Py_False;
	}
	//memset(display_buffer, 0, sizeof(display_buffer));
	memset(display_buffer, 0, 160*81);

	for (i = 0; i < nCList; i++) {
		pListItem = PyList_GetItem(pList, i);
		pos = 0;
#if 0
		display_buffer[i*81] = 0x00;
		
		//增加图片置中显示代码
		for (j = 0; j < PyList_Size(pListItem); j++) {
			pItem = PyList_GetItem(pListItem, j);

			if ((j % 2) != 0)
				pos++;
			
			val = (unsigned char)PyLong_AsLong(pItem);

			if (j % 2 != 0)
				display_buffer[i*81 + pos] |= (val << 4);
			else
				display_buffer[i*81 + pos] |= val;
		}
		
		display_buffer[(i+1)*81 - 1] &= ~0xf;
#else
		for (j = 0; j < PyList_Size(pListItem); j++) {
			pItem = PyList_GetItem(pListItem, j);
			val = (unsigned char)PyLong_AsLong(pItem);
			
			if ((j!=0) && (j%2 == 0))
				pos++;

			if (j%2 != 0)
				display_buffer[i*81 + pos] |= val;
			else
				display_buffer[i*81 + pos] |= (val << 4);
		}
#endif	
		//PyObject_Print(pListItem, stdout, 0);
		//if(PyLong_Check(pListItem)) {
	}

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
	
	PyMem_Free(display_buffer);
#endif
	
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
	//printf("spilcd\n");
	return PyModule_Create(&spilcdPyDem);
}
