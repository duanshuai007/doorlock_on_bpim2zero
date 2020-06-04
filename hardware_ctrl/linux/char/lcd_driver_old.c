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

/*
 *	因为BPIM2zero 固件只有SPI0的驱动，没有SPI1的驱动
 *	lcd屏幕需要SPI的驱动，又接在了SPI1接口上，所以选择模拟SPI的方式进行驱动
 */

#define PIN_SDA		15	//PA15
#define PIN_SCK		14	//PA14
#define PIN_RST		16	//PA16
#define PIN_A0		21	//PA21
#define PIN_CS		13	//PA13

#define SPI_1_REG_ADDR	0x01C68000

typedef struct pin_desc_t {
	int sda;	//数据输出线
	int sck;	//时钟线
	int rst;	//复位线
	int a0;		//指令数据切换线
	int cs;		//片选线
} pin_desc_t;

#define USE_LED 1

/*
static char *name = "bigfish";
module_param(name, charp, S_IRUGO);
MODULE_PARM_DESC(name, "name,type: char *, permission:S_IRUGO");
static int watchdog = 1000;
module_param(watchdog, int, 0644);
MODULE_PARM_DESC(watchdog, "set watchdog timeout on million seconds");
*/

#define DEFAULT_MAJOR	0

typedef struct spi_reg_t {
	unsigned long dummy0;
	unsigned long gcr;
	unsigned long tcr;
	unsigned long dummy1;
	unsigned long ier;
	unsigned long isr;
	unsigned long fcr;
	unsigned long fsr;
	unsigned long wcr;
	unsigned long ccr;
	unsigned long dummy2;
	unsigned long dummy3;
	unsigned long mbc;
	unsigned long mtc;
	unsigned long bcc;
	unsigned long dummyarray1[113];
	unsigned long txd;
	unsigned long dummyarray2[63];
	unsigned long rxd;
} spi_reg_t;

typedef struct lcd_t {
	int dev_major;
	struct class *class;
	struct cdev *cdev;
	struct device *device;
	struct pin_desc_t pin;
	struct spi_reg_t *reg;
	//wait_queue_head_t read_queue;
	//wait_queue_head_t write_queue;
	//struct timer_list pin_timer;
	struct kobject *kobj;
	//int timer_open_flag;
	int pin_irq_number;
	char buffer[1024];
} lcd_t;

static lcd_t *lcd = NULL;

//kobject OPS
//该函数被__ATTR_RO(name)自动扩展为${name}_show
static ssize_t led_show(struct kobject *kobjs, struct kobj_attribute *attr, char *buf) {
	printk(KERN_INFO "read led\n");
	int val = gpio_get_value(lcd->pin.cs);
	return sprintf(buf, "the led status = %d\n", val);
}

//这两个函数被_ATTR
static ssize_t led_status_show(struct kobject *kobjs, struct kobj_attribute *attr, char *buf) {
	printk(KERN_INFO "led status show\n");
	int val = gpio_get_value(lcd->pin.cs);
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

// /dev/led驱动代码
#if USE_LED
static void gpio_config(struct pin_desc_t *ppin) {
	if (!gpio_is_valid(ppin->cs)) {
		printk(KERN_ALERT "error wrong gpio number!\n");
		return;
	}
	gpio_request(ppin->cs, "lcd_cs");
	gpio_direction_output(ppin->cs, 1);
	gpio_set_value(ppin->cs, 1);

#if 0
	if (!gpio_is_valid(INTERRUPT_PIN)) {
		printk(KERN_ALERT "error wrong interrupt pin!\n");
		return -ENODEV;
	}
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
	gpio_free(lcd->pin.cs);
}
#endif

static void pin_timer_handler(unsigned long data)
{
	printk(KERN_INFO "enter timer! data=%d", (int)data);
	
}
#if USE_LED
static irqreturn_t pin_irq_handle(int irq, void *devid)
{
	printk(KERN_INFO "enter ieq, devid=%d!\n", (int)devid);

	return (irqreturn_t)IRQ_HANDLED;
}
#endif
static int led_open(struct inode *node, struct file *file)
{
	printk(KERN_INFO "led open\n");
	file->private_data = (void *)lcd;

#if USE_LED
	gpio_config(&lcd->pin);
#endif
	return 0;
}

static ssize_t led_read(struct file *file, char *buf, size_t count, loff_t *pos)
{
	int ret = 0;
	lcd_t *p = (lcd_t *)file->private_data;
	int val = gpio_get_value(p->pin.cs);
	ret = copy_to_user(buf, &val, 1);
	if (ret == 0)
		return 0;
	else {
		printk(KERN_ALERT "error occur when reading!\n");
		return -EFAULT;
	}
	return 1;
}

static ssize_t led_write(struct file *file, const char *buf, size_t count, loff_t *pos)
{
	int ret = 0;
	lcd_t *p = (lcd_t *)file->private_data;

	if (count > sizeof(p->buffer)) {
		printk(KERN_ALERT "count too big, should less than\n");
		return -EFAULT;
	}
	
	ret = copy_from_user(p->buffer, buf, count);
	if (ret == 0) {
		if (memcmp(p->buffer, "on", 2) == 0) {
			printk(KERN_INFO "led on!\n");
			gpio_set_value(lcd->pin.cs, 1);
		} else if (memcmp(p->buffer, "off", 3) == 0) {
			printk(KERN_INFO "led off!\n");
			gpio_set_value(lcd->pin.cs, 0);
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

static int led_release(struct inode *node, struct file *file)
{
	printk(KERN_INFO "led release\n");
	file->private_data = NULL;
#if USE_LED
	gpio_deconfig();
#endif
	return 0;
}

static struct file_operations led_ops = {
	.owner = THIS_MODULE,
	.open = led_open,
	.release = led_release,
	.read = led_read,
	.write = led_write,
};


static int __init lcd_driver_init(void) 
{
	int ret = 0;
	dev_t devno;

	//printk("input name : %s", name);
	//printk("watch dog timeout : %d\n", watchdog);
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

	//字符设备注册
	if (lcd->dev_major > 0) {
		devno = MKDEV(lcd->dev_major, 0);
		ret = register_chrdev_region(devno, 1, "led_zy");
	} else {
		ret = alloc_chrdev_region(&devno, 0, 1, "led_zy");
		lcd->dev_major = MAJOR(devno);
	}
	if (ret < 0) {
		printk(KERN_ALERT "dev major failed\n");
		return -EFAULT;
	}

	printk(KERN_INFO "major = %d\n", lcd->dev_major);
	//CREATE DEVICE CLASS
	lcd->class = class_create(THIS_MODULE, "led_class");
	if (IS_ERR(lcd->class)) {
		printk(KERN_ALERT "class create failed\n");
		unregister_chrdev_region(MKDEV(lcd->dev_major, 0), 1);
		return PTR_ERR(lcd->class);
	}

	lcd->cdev = cdev_alloc();
	cdev_init(lcd->cdev, &led_ops);
	ret = cdev_add(lcd->cdev, devno, 1);
	if (ret) {
		class_destroy(lcd->class);
		unregister_chrdev_region(MKDEV(lcd->dev_major, 0), 1);
		printk(KERN_ALERT "cdev add failed\n");
		return -EFAULT;
	}
	printk(KERN_INFO "devno=%d major=%d\n", devno, MKDEV(lcd->dev_major, 0));
	lcd->device = device_create(lcd->class, NULL, devno, NULL, "spilcd");

	if (IS_ERR(lcd->device)) {
		cdev_del(lcd->cdev);
		class_destroy(lcd->class);
		unregister_chrdev_region(MKDEV(lcd->dev_major, 0), 1);
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
	cdev_del(lcd->cdev);
	class_destroy(lcd->class);

	unregister_chrdev_region(MKDEV(lcd->dev_major, 0), 1);
}

module_init(lcd_driver_init);
module_exit(lcd_driver_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("duanshuai");
MODULE_DESCRIPTION("linux kernel driver - lcd driver simulation spi");
MODULE_VERSION("0.1");
