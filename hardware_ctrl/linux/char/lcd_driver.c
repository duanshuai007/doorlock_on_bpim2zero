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

#define SPI_1_REG_ADDR	0x01C69000

#define READREG(addr) ((unsigned int *)((addr)))

typedef struct pin_desc_t {
	int sda;	//数据输出线
	int sck;	//时钟线
	int rst;	//复位线
	int a0;		//指令数据切换线
	int cs;		//片选线
} pin_desc_t;


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
	unsigned int dummy0;
	unsigned int gcr;
	unsigned int tcr;
	unsigned int dummy1;
	unsigned int ier;
	unsigned int isr;
	unsigned int fcr;
	unsigned int fsr;
	unsigned int wcr;
	unsigned int ccr;
	unsigned int dummy2;
	unsigned int dummy3;
	unsigned int mbc;
	unsigned int mtc;
	unsigned int bcc;
	unsigned int dummyarray1[113];
	unsigned int txd;
	unsigned int dummyarray2[63];
	unsigned int rxd;
} spi_reg_t;

typedef struct lcd_t {
	int dev_major;
	struct class *class;
	struct cdev *cdev;
	struct device *device;
	struct pin_desc_t pin;
	void __iomem *regbase;
	struct spi_reg_t *reg;
	void __iomem *clkreg;
	void __iomem *pioreg;
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

// /dev/led驱动代码
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

static void pin_timer_handler(unsigned long data)
{
	printk(KERN_INFO "enter timer! data=%d", (int)data);
	
}
static irqreturn_t pin_irq_handle(int irq, void *devid)
{
	printk(KERN_INFO "enter ieq, devid=%d!\n", (int)devid);

	return (irqreturn_t)IRQ_HANDLED;
}

static void spi_config(struct spi_reg_t *preg)
{
	//clear spi controller
	//preg->gcr |= (1<<31);
	//while(preg->gcr | (1<<31));
	//lcd->clkreg = (unsigned long)ioremap(0x01C20000, 0x400);
	//lcd->pioreg = (unsigned long)ioremap(0x01C20800, 0x400);

	unsigned int val;

	*READREG(lcd->clkreg + 0xA4) = 0x81000005;
	//set SPI1_RST De-assert
	val = *READREG(lcd->clkreg + 0x02c0);
	printk(KERN_INFO "BUS_SOFT_RST_REG0 = %08x\n", val);
	val |= (1 << 21);
	*READREG(lcd->clkreg + 0x02c0) = val;
	printk(KERN_INFO "BUS_SOFT_RST_REG0 = %08x\n", *READREG(lcd->clkreg + 0x02c0));
	
	//set spi1 clk gating
	val =  *READREG(lcd->clkreg + 0x0060);
	printk(KERN_INFO "BUS_CLK_GATING_REG = %08x\n", val);
	val |= (1 << 21);
	*READREG(lcd->clkreg + 0x0060) = val;
	printk(KERN_INFO "BUS_CLK_GATING_REG = %08x\n", *READREG(lcd->clkreg + 0x0060));

	//set spi gpio function
	val = *READREG(lcd->pioreg + 0x04);
	//pa14 as spi1 clk
	val &= ~(0x7 << 24);
	val |= (2 << 24);
	//pa15 as spi mosi
	val &= ~(0x7 << 28);
	val |= (2 << 24);
	//pa13 as spi cs
	val &= ~(0x7 << 20);
	val |= (2 << 20);
	*READREG(lcd->pioreg + 0x04) = val;

	//pa16 as spi miso
	val = *READREG(lcd->pioreg + 0x08);
	val &= ~(0x7 << 0);
	val |= (2 << 0);
	*READREG(lcd->pioreg + 0x08) = val;

	//preg->tcr = 0x1c4;
	//cpha 0 (leading edge for sample data)
	//cpol 0 (active high polarity)
	//ss set software, and sslevel set 1 (must)
	preg->tcr = (0 << 1) | (0 << 1) | (1 << 2) | (1 << 6) | (1 << 7);
	preg->ier = 0;
	preg->isr = 0;
	//disable rxfifo dma request
	//disable txfifo dma request
	preg->fcr = (0 << 8) | (0 << 24);
	preg->wcr = 0;
	//设置时钟
	preg->ccr = 0x1004;


	preg->mbc = 1;
	preg->mtc = 1;
	preg->bcc = 1;
	/*
	397     u32 reg_val = readl(base_addr + SPI_BURST_CNT_REG);
	398 
	399     reg_val &= ~SPI_BC_CNT_MASK;
	400     reg_val |= (SPI_BC_CNT_MASK & (tx_len + rx_len + dummy_cnt));
	401     writel(reg_val, base_addr + SPI_BURST_CNT_REG);
	402 
	403     reg_val = readl(base_addr + SPI_TRANSMIT_CNT_REG);
	404     reg_val &= ~SPI_TC_CNT_MASK;
	405     reg_val |= (SPI_TC_CNT_MASK & tx_len);
	406     writel(reg_val, base_addr + SPI_TRANSMIT_CNT_REG);
	407 
	408     reg_val = readl(base_addr + SPI_BCC_REG);
	409     reg_val &= ~SPI_BCC_STC_MASK;
	410     reg_val |= (SPI_BCC_STC_MASK & stc_len);
	411     reg_val &= ~(0xf << 24);
	412     reg_val |= (dummy_cnt << 24);
	413     writel(reg_val, base_addr + SPI_BCC_REG);
*/
	//stop transmit data when rxfifo full
	//master mode
	//enable
	preg->gcr = (0 << 7) | (1 << 1) | (1 << 0);
	printk(KERN_INFO "spi0clk= %08x\n", *READREG(lcd->clkreg + 0xA4));
}

static void printk_reg(void)
{
	printk(KERN_INFO " GCR = %08x\n "
					 " TCR = %08x\n "
					 " IER = %08x\n "
					 " ISR = %08x\n "
					 " FCR = %08x\n "
					 " FSR = %08x\n "
					 " WCR = %08x\n "
					 " CCR = %08x\n "
					 " MBC = %08x\n "
					 " MTC = %08x\n "
					 " BCC = %08x\n "
					 " TXD = %08x\n "
					 " RXD = %08x\n ",
						lcd->reg->gcr,
						lcd->reg->tcr,
						lcd->reg->ier,
						lcd->reg->isr,
						lcd->reg->fcr,
						lcd->reg->fsr,
						lcd->reg->wcr,
						lcd->reg->ccr,
						lcd->reg->mbc,
						lcd->reg->mtc,
						lcd->reg->bcc,
						lcd->reg->txd,
						lcd->reg->rxd
		  );
}
static int lcd_open(struct inode *node, struct file *file)
{
	printk(KERN_INFO "led open\n");
	file->private_data = (void *)lcd;

	//printk(KERN_INFO "gpio config\n");
	//gpio_config(&lcd->pin);

	printk(KERN_INFO "spi config\n");
	spi_config(lcd->reg);

	printk_reg();

	return 0;
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
	unsigned char time;
	int fifocnt;
	
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
			gpio_set_value(lcd->pin.cs, 1);
		} else if (memcmp(p->buffer, "off", 3) == 0) {
			printk(KERN_INFO "led off!\n");
			gpio_set_value(lcd->pin.cs, 0);
			printk(KERN_INFO "fsr addr=%08x txdaddr=%08x\n", &lcd->reg->fsr, &lcd->reg->txd);
			//clear irq pending
			p->reg->isr = 0x77 | (0x3f << 8);
			//disable tx dma request and rx dma request
			p->reg->fcr &= ~((1 << 8) | (1<<24));
			//reset fifo 
			p->reg->fcr |= (1 << 15) | (1 << 31);
			p->reg->fcr &= ~(0xff | 0xff << 16);
			p->reg->fcr |= (0x20) | 0x20 << 16;

			while (len > 0) {
				fifocnt = (lcd->reg->fsr >> 16) & 0xff;
				if (fifocnt >= 64) {
					for (time = 5; time > 0; time--);			
				}
				printk(KERN_INFO "fifo count = %d\n", fifocnt);
				//lcd->reg->txd = p->buffer[count - len];
				writeb(p->buffer[count - len], lcd->regbase + 0x200);
				printk(KERN_INFO "fifo txd = %c\n", lcd->reg->txd);
				len--;
			}

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
#if 1
	lcd->regbase = ioremap(SPI_1_REG_ADDR, 0x400);
	//lcd->reg = (struct spi_reg_t *)ioremap(SPI_1_REG_ADDR, 0x400);
	lcd->reg = (struct spi_reg_t *)lcd->regbase;
	printk(KERN_INFO " GCR = %08x\n " \
					 " TCR = %08x\n " \
					 " IER = %08x\n " \
					 " ISR = %08x\n " \
					 " FCR = %08x\n " \
					 " FSR = %08x\n " \
					 " WCR = %08x\n " \
					 " CCR = %08x\n " \
					 " MBC = %08x\n " \
					 " MTC = %08x\n " \
					 " BCC = %08x\n " \
					 " TXD = %08x\n " \
					 " RXD = %08x\n ", 
						lcd->reg->gcr,
						lcd->reg->tcr,
						lcd->reg->ier,
						lcd->reg->isr,
						lcd->reg->fcr,
						lcd->reg->fsr,
						lcd->reg->wcr,
						lcd->reg->ccr,
						lcd->reg->mbc,
						lcd->reg->mtc,
						lcd->reg->bcc,
						lcd->reg->txd,
						lcd->reg->rxd
		  );
	lcd->clkreg = ioremap(0x01C20000, 0x400);
	lcd->pioreg = ioremap(0x01C20800, 0x400);
	printk(KERN_INFO "SPI0CLK: %08x\nSPI1CLK: %08x\n", \
							*READREG(lcd->clkreg + 0xA0), \
							*READREG(lcd->clkreg + 0xA4));
#endif
#if 0
	unsigned long spi0base = (unsigned long)ioremap(0x01C68000, 0x400);
	struct spi_reg_t *preg = (struct spi_reg_t *)spi0base;
	printk(KERN_INFO " GCR = %08x\n "
					 " TCR = %08x\n "
					 " IER = %08x\n "
					 " ISR = %08x\n "
					 " FCR = %08x\n "
					 " FSR = %08x\n "
					 " WCR = %08x\n "
					 " CCR = %08x\n "
					 " MBC = %08x\n "
					 " MTC = %08x\n "
					 " BCC = %08x\n "
					 " TXD = %08x\n "
					 " RXD = %08x\n ",
					 *READREG(spi0base + 0x04),
					 *READREG(spi0base + 0x08),
					 *READREG(spi0base + 0x10),
					 *READREG(spi0base + 0x14),
					 *READREG(spi0base + 0x18),
					 *READREG(spi0base + 0x1C),
					 *READREG(spi0base + 0x20),
					 *READREG(spi0base + 0x24),
					 *READREG(spi0base + 0x30),
					 *READREG(spi0base + 0x34),
					 *READREG(spi0base + 0x38),
					 *READREG(spi0base + 0x200),
					 *READREG(spi0base + 0x300)
		  );

	//*READREG(spi0base + 0x200) = 0x55;
	//printk(KERN_INFO "TXD = %08x\n", preg->txd);
	//printk(KERN_INFO "TXD 1 = %08x\n", *READREG(spi0base + 0x200));
	//printk(KERN_INFO "TXD = %08x RXD = %08x\n", &preg->txd, &preg->rxd);
	//printk(KERN_INFO "TXD 2 = %08x addr= %08x\n", *READREG(spi0base + 0x200), READREG(spi0base + 0x200));

	*READREG(spi0base + 0x200) = 0x55;
	printk(KERN_INFO "TXD1 = %08x\n", preg->txd);
	preg->txd = 0x88;
	printk(KERN_INFO "TXD2 = %08x\n", preg->txd);
#endif

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
