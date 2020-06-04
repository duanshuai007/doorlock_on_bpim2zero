#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kobject.h>
#include <linux/sysfs.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/interrupt.h>
#include <linux/gpio.h>
#include <linux/uaccess.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/delay.h>


/*
 *	因为BPIM2zero 固件只有SPI0的驱动，没有SPI1的驱动
 *	lcd屏幕需要SPI的驱动，又接在了SPI1接口上，所以选择模拟SPI的方式进行驱动
 */

#define PIN_SDA		15	//PA15
#define PIN_SCK		14	//PA14
#define PIN_RST		16	//PA16
#define PIN_A0		21	//PA21
#define PIN_CS		13	//PA13

#define SPI_1_REG_ADDR	0x01C69000

#define READREG(addr) ((unsigned int *)((addr)))

#define CS_ENABLE	0
#define CS_DISABLE	1
#define A0_CMD		0
#define A0_DATA		1
#define RST_ENABLE	0
#define RST_DISABLE	1

#define R0	0x24
#define R1	0x28
#define R2	0x81
#define	R3	0xE8
#define R4	0xA0
#define R5	0xA4
#define R6	0xA6
#define R7	0xA8
#define R8	0xC0
#define R9	0xC8
#define R10	0xD8
#define R11	0xD0
#define R12	0xD4
#define R13	0xE2
#define R14	0xE3
#define R15	0xF1


typedef struct pin_desc_t {
	int sda;	//数据输出线
	int sck;	//时钟线	空闲时为高电平
	int rst;	//复位线 低电平复位，最小时间3us，复位到重新启动时间200ms
	int a0;		//指令数据切换线 低电平指令 高电平数据
	int cs;		//片选线	低电平有效
} pin_desc_t;

#define DEFAULT_MAJOR	0

typedef struct lcd_t {
	int dev_major;
	struct class *class;
	struct cdev *cdev;
	struct device *device;
	struct pin_desc_t pin;
	void __iomem *pioreg;
	struct kobject *kobj;
	int pin_irq_number;
	char buffer[1024];
} lcd_t;

static lcd_t *lcd = NULL;

//kobject OPS
//该函数被__ATTR_RO(name)自动扩展为${name}_show
static ssize_t led_show(struct kobject *kobjs, struct kobj_attribute *attr, char *buf) {
	int val;
	printk(KERN_INFO "read led\n");
	val = gpio_get_value(lcd->pin.cs);
	return sprintf(buf, "the led status = %d\n", val);
}

//这两个函数被_ATTR
static ssize_t led_status_show(struct kobject *kobjs, struct kobj_attribute *attr, char *buf) {
	int val;
	printk(KERN_INFO "led status show\n");
	val = gpio_get_value(lcd->pin.cs);
	return sprintf(buf, "led status = %d\n", val);
}

static ssize_t led_status_store(struct kobject *kobj, struct kobj_attribute *attr, const char *buf, size_t count) 
{
	printk(KERN_INFO "led status store\n");
	if (0 == memcmp(buf, "on", 2)) {
		gpio_set_value(lcd->pin.cs, 1);
	} else if (0 == memcmp(buf, "off", 3)) {
		gpio_set_value(lcd->pin.cs, 0);
	} else {
		printk(KERN_INFO "Not support cmd\n");
	}

	return count;
}

static struct kobj_attribute status_attr = __ATTR_RO(led);
static struct kobj_attribute led_attr = __ATTR( led_status, 0660, led_status_show, led_status_store);

static struct attribute *led_attrs[] = {
	&status_attr.attr,
	&led_attr.attr,
	NULL,
};

static struct attribute_group attr_g = {
	.name = "kobject_led",
	.attrs = led_attrs,
};


static void write_data(unsigned char dat)
{
	int i;

	gpio_set_value(lcd->pin.cs, CS_ENABLE);
	gpio_set_value(lcd->pin.a0, A0_DATA);
	ndelay(220);

	for (i = 0; i < 8; i++) {
		gpio_set_value(lcd->pin.sck, 0);	
		if ((dat & 0x80) == 0)
			gpio_set_value(lcd->pin.sda, 0);
		else
			gpio_set_value(lcd->pin.sda, 1);
		ndelay(50);
		gpio_set_value(lcd->pin.sck, 1);	
		dat <<= 1;
		ndelay(50);
	}
	ndelay(50);
	gpio_set_value(lcd->pin.cs, CS_DISABLE);
}

static void write_cmd(unsigned char cmd)
{
	int i;

	gpio_set_value(lcd->pin.cs, CS_ENABLE);
	gpio_set_value(lcd->pin.a0, A0_CMD);
	ndelay(220);

	for (i = 0; i < 8; i++) {
		gpio_set_value(lcd->pin.sck, 0);
		if ((cmd & 0x80) == 0)
			gpio_set_value(lcd->pin.sda, 0);
		else
			gpio_set_value(lcd->pin.sda, 1);
		ndelay(50);
		gpio_set_value(lcd->pin.sck, 1);
		ndelay(50);
		cmd <<= 1;
	}
	ndelay(50);
	gpio_set_value(lcd->pin.cs, CS_DISABLE);
}

static void lcd_reset(void)
{
	gpio_set_value(lcd->pin.rst, RST_ENABLE);
	ndelay(20);
	gpio_set_value(lcd->pin.rst, RST_DISABLE);
	mdelay(210);
}

//col: 0 - 54
static void set_lcd_column(unsigned char col)
{
	if (col > 54) {
		printk(KERN_ALERT "lcd col error, col=%d\n", col); 
		return;
	}
	unsigned char realcol = col + 37;

	write_cmd(0x00 | 0x0f & realcol);
	write_cmd(0x10 | ((realcol >> 4) & 0x0f));
}

//row:0-159
static void set_lcd_row(unsigned char row)
{
	if (row > 159) {
		printk(KERN_ALERT "lcd row error, row=%d\n", row);
		return;
	}

	write_cmd(0x40 | (row & 0x0f));
	write_cmd(0x70 | ((row >> 4) & 0x0f));
}

/*
 *	(0)automodify: 1=行列到达边界时自动修改 0=不自动修改到达边界后不变
 *	(1)modifymode: 1=colmode 0=rowmode
 *	(2)rowmodifymode: 0=+1 1=-1
 */
static void set_r18(unsigned char automodify, unsigned char modifymode, unsigned char rowmodifymode)
{
	write_cmd(0x88 | ((automodify << 0) | (modifymode << 1) | (rowmodifymode << 2)));
}

static void lcd_window_init(unsigned char start_row, unsigned char start_col, unsigned char width, unsigned char height)
{
	if (start_row > 159 || (start_row + height > 160)) {
		printk(KERN_ALERT "lcd_window_init row error,start=%d,height=%d\n", start_row, height);
		return;
	}

	if (start_col > 54 || (start_col + width > 54)) {
		printk(KERN_ALERT "lcd_window_init col error,start=%d,height=%d\n", start_col, width);
		return;
	}

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
	mdelay(200);

	//设置温度补偿系数:00
	write_cmd(0x24 | 0);
	
	//电源控制设置
	//pc0:0->承受lcd负载<=13nF, 1->承受lcd负载为13nF<lcd<=22nF
	//pc1:0->关闭内置升压电路, 1->启用内部升压电路
	write_cmd(0x28 | 2);

	//设置对比度电压 取值范围0-255
	write_cmd(0x81);
	write_cmd(188);

	//偏压比设置 取值范围0-3
	write_cmd(0xe8 | 1);

	//设置帧率 取值范围0-3
	write_cmd(0xa0 | 2);
	
	//设置全显示 0->关闭全显示 1->打开全显示
	write_cmd(0xa4 | 0);

	//设置负性显示 0关闭 1开启
	write_cmd(0xa6 | 0);

	//lcd映像设置
	write_cmd(0xc0);

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

	//显示使能设置
	//(0): 1开显示 0关显示
	//(1): 1开启灰度显示 0关闭灰度显示
	//(2): 1关闭增强模式 0开启增强模式
	write_cmd(0xa8 | (1<<0) | (0 << 1) | (0 << 2));
	//该指令执行后需要延时10毫秒不操作lcd模块来保证不对模块造成有害的干扰
	mdelay(20);
}

// /dev/led驱动代码
static void gpio_config(struct pin_desc_t *ppin) 
{
	if (	!gpio_is_valid(ppin->sda) || !gpio_is_valid(ppin->sck) || 
			!gpio_is_valid(ppin->a0 ) || !gpio_is_valid(ppin->rst) ||
			!gpio_is_valid(ppin->cs )
		) 
	{
		printk(KERN_ALERT "error wrong gpio number!\n");
		return;
	}
	
	gpio_request(ppin->sda, "lcd_sda");
	gpio_direction_output(ppin->sda, 1);
	gpio_set_value(ppin->sda, 1);

	gpio_request(ppin->sck, "lcd_sck");
	gpio_direction_output(ppin->sck, 1);
	gpio_set_value(ppin->sck, 1);

	gpio_request(ppin->a0, "lcd_a0");
	gpio_direction_output(ppin->a0, 1);
	gpio_set_value(ppin->a0, 1);

	gpio_request(ppin->rst, "lcd_rst");
	gpio_direction_output(ppin->rst, 1);
	gpio_set_value(ppin->rst, RST_DISABLE);

	gpio_request(ppin->cs, "lcd_cs");
	gpio_direction_output(ppin->cs, 1);
	gpio_set_value(ppin->cs, CS_DISABLE);
#if 0
	gpio_request(INTERRUPT_PIN, "interrupt_pin");
	gpio_direction_input(INTERRUPT_PIN);
	//设置pin消抖时间20MS
	gpio_set_debounce(INTERRUPT_PIN, 20);
	pin_irq_number = gpio_to_irq(INTERRUPT_PIN);
	printk(KERN_INFO "pin irq number = %d", pin_irq_number);
	ret = request_irq(pin_irq_number, 
						(irq_handler_t)pin_irq_handle,
						IRQF_TRIGGER_RISING,
						"pin irq",
						NULL);
#endif
}

static void gpio_deconfig(void) {
	gpio_free(lcd->pin.sda);
	gpio_free(lcd->pin.sck);
	gpio_free(lcd->pin.a0);
	gpio_free(lcd->pin.rst);
	gpio_free(lcd->pin.cs);
}

static void pin_timer_handler(unsigned long data)
{
	printk(KERN_INFO "enter timer! data=%d", (int)data);
}

static irqreturn_t pin_irq_handle(int irq, void *devid)
{
	printk(KERN_INFO "enter irq, devid=%d!\n", (int)devid);

	return (irqreturn_t)IRQ_HANDLED;
}

static int lcd_open(struct inode *node, struct file *file)
{
	printk(KERN_INFO "led open\n");
	file->private_data = (void *)lcd;

	printk(KERN_INFO "gpio config\n");
	gpio_config(&lcd->pin);

	lcd_init();
	return 0;
}

static int display_full_window(unsigned char status)
{
	int i, j;

	lcd_window_init( 0, 0, 54, 159);
	lcd_window_enable(true);

	for (i = 0; i < 160; i++) {
		for (j = 0; j < 54; j++) {
			write_data(status);
			write_data(status);
			write_data(status);
		}
	}
	lcd_window_enable(false);
}

static ssize_t lcd_read(struct file *file, char *buf, size_t count, loff_t *pos)
{
	int ret = 0;
	int val;
	lcd_t *p = (lcd_t *)file->private_data;
	val = gpio_get_value(p->pin.cs);
	ret = copy_to_user(buf, &val, 1);
	if (ret == 0)
		return 0;
	else {
		printk(KERN_ALERT "error occur when reading!\n");
		return -EFAULT;
	}
	return 1;
}



static ssize_t lcd_write(struct file *file, const char *buf, size_t count, loff_t *pos)
{
	int ret = 0;
	int len;
	
	lcd_t *p = (lcd_t *)file->private_data;

	if (count > sizeof(p->buffer)) {
		printk(KERN_ALERT "count too big, should less than\n");
		return -EFAULT;
	}
	
	len = count;

	ret = copy_from_user(p->buffer, buf, count);
	if (ret == 0) {
		if (memcmp(p->buffer, "on", 2) == 0) {
			printk(KERN_INFO "led on!\n");
			display_full_window(0);
		} else if (memcmp(p->buffer, "off", 3) == 0) {
			printk(KERN_INFO "led off!\n");
			display_full_window(0xff);
		} else {
			printk(KERN_INFO "cmd error\n");
			return -EFAULT;
		}
	} else {
		printk(KERN_ALERT "error occur when writing!\n");
		return -EFAULT;
	}

	return count;
}

static int lcd_release(struct inode *node, struct file *file)
{
	printk(KERN_INFO "led release\n");
	file->private_data = NULL;
	gpio_deconfig();

	return 0;
}

static struct file_operations led_ops = {
	.owner = THIS_MODULE,
	.open = lcd_open,
	.release = lcd_release,
	.read = lcd_read,
	.write = lcd_write,
};

static int __init lcd_driver_init(void)
{
	int ret = 0;

	printk(KERN_DEBUG "lcd driver!!!\n");

	lcd = kmalloc(sizeof(lcd_t), GFP_KERNEL);
	if (!lcd) {
		printk(KERN_ALERT "kmalloc failed\n");
		return -ENOMEM;
	}

	lcd->dev_major = DEFAULT_MAJOR;
	lcd->pin.sda	= PIN_SDA;
	lcd->pin.sck	= PIN_SCK;
	lcd->pin.rst	= PIN_RST;
	lcd->pin.a0		= PIN_A0;
	lcd->pin.cs		= PIN_CS;

	//创建kobj结构体
	lcd->kobj = kobject_create_and_add("lcd_obj_test", kernel_kobj->parent);
	if (!lcd->kobj) {
		printk(KERN_ALERT "kobject_create_and_add failed\n");
		return -1;
	}
	
	ret = sysfs_create_group(lcd->kobj, &attr_g);
	if (ret) {
		printk(KERN_ALERT "sysfs_create_group failed\n");
	}

	lcd->dev_major = register_chrdev(lcd->dev_major, "led_zy", &led_ops);
	if (lcd->dev_major < 0) {
		printk(KERN_ALERT "register chrdev failed\n");
		return ret;
	}
	
	printk(KERN_INFO "major = %d\n", lcd->dev_major);
	//CREATE DEVICE CLASS
	lcd->class = class_create(THIS_MODULE, "spilcd");	//对应/sys/class/spilcd
	if (IS_ERR(lcd->class)) {
		printk(KERN_ALERT "class create failed\n");
		unregister_chrdev(MKDEV(lcd->dev_major, 0), "led_zy");
		return PTR_ERR(lcd->class);
	}

	printk(KERN_INFO "devno=%d\n", MKDEV(lcd->dev_major, 0));
	lcd->device = device_create(lcd->class, NULL, MKDEV(lcd->dev_major, 0), NULL, "spilcd"); //对应/dev/spilcd

	if (IS_ERR(lcd->device)) {
		class_destroy(lcd->class);
		unregister_chrdev(MKDEV(lcd->dev_major, 0), "led_zy");
		printk(KERN_ALERT "device create failed\n");
		return PTR_ERR(lcd->device);
	}

	//setup_timer(&lcd->pin_timer, &pin_timer_handler, 0);

	return 0;
}

static void __exit lcd_driver_exit(void)
{
	printk(KERN_DEBUG "lcd driver exit!!!\n");

	kobject_put(lcd->kobj);

	device_destroy(lcd->class, MKDEV(lcd->dev_major, 0));
	class_destroy(lcd->class);
	unregister_chrdev(MKDEV(lcd->dev_major, 0), "led_zy");
}

module_init(lcd_driver_init);
module_exit(lcd_driver_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("duanshuai");
MODULE_DESCRIPTION("linux kernel driver - lcd driver simulation spi");
MODULE_VERSION("0.1");
