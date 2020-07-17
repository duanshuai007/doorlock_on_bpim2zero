# 代码安全

---


为了充分保障代码安全，防止代码泄漏，本程序中的`python`代码在发布时仅仅将经过编译后的`*.so`文件经过`tar`加密打包后上传到服务器。

## 1. Python代码编译为so文件

#### setup.py

```
from distutils.core import setup,Extension
from Cython.Build import cythonize

setup(  
		name='python_modules',
		version='1.0',
		platforms='arm',
		description='doorlock python modules',
		author='bigfish',
		author_email='duanbixing@163.com',
		ext_modules=cythonize([ 
			"watchdog/watchdog.c", 
			"config/config.py"
		])  
	 )  
```

在执行`python3 setup.py build` 时会将`watchdog/watchdog.c`和`config/config.py`分别编译成so文件，并生成在`build/lib.linux-x86_64-3.5/`目录下。

* ps:在本项目中在ubuntu主机上生成的so名字格式为`config.cpython-35m-x86_64-linux-gnu.so`，该名字的文件放在目标设备上的`/usr/local/lib/python3.5/dist-packages/`目录下不能正确识别，需要将名字改为`config.so`这种格式才会正确识别。

## 2.生成的目标程序目录加密打包

#### 注意:加密的密码为message_struct.py中的DOORSTONE的值!

在`message_struct.py`中`DOORSTONE="iotwonderful"`

在shell脚本中读取DOORSTONE的值为"iotwonderful"

在脚本中通过  
`tar -zcvf - ${target} | openssl des3 -salt -k ${tarpassword} | dd of=firmware_${version}.des3.tar.gz`
来对目标文件进行加密打包。

我们使用  
`dd if=firmware_14.des3.tar.gz  | openssl des3 -d -k "iotwonderful" | tar zxvf -` 来进行解压发现无法正确解压。

再次使用
`dd if=firmware_14.des3.tar.gz  | openssl des3 -d -k \"iotwonderful\" | tar zxvf -`
发现能够正确解压

所以在`python`代码`python_modules/uncompressfirmware/uncompressfirmware.py`中，构建解压的cmd字符串时需要注意，要使用如下格式来进行生成。  
`cmd = "dd if={} | openssl des3 -d -k {}{}{} | tar zxvf - > /dev/null".format(gzfile, "\\\"", salt, "\\\"")`


## 3.生成升级包

在项目的根目录下执行`sudo ./build_firmware.sh [version number]` 即可生成对应版本信息的固件文件，文件名不可以修改，会影响设备升级。

