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
#include <asm/io.h>


/*
 *	因为BPIM2zero 固件只有SPI0的驱动，没有SPI1的驱动
 *	lcd屏幕需要SPI的驱动，又接在了SPI1接口上，所以选择模拟SPI的方式进行驱动
 */
#define PIN_SDA		15	//PA15
#define PIN_SCK		14	//PA14
#define PIN_RST		16	//PA16
#define PIN_A0		21	//PA21
#define PIN_CS		13	//PA13

//#define SPI_1_REG_ADDR	0x01C69000
//#define READREG(addr) ((unsigned int *)((addr)))

#define CS_ENABLE	0
#define CS_DISABLE	1
#define A0_CMD		0
#define A0_DATA		1
#define RST_ENABLE	0
#define RST_DISABLE	1

typedef struct pin_desc_t {
	int sda;	//数据输出线
	int sck;	//时钟线	空闲时为高电平
	int rst;	//复位线 低电平复位，最小时间3us，复位到重新启动时间200ms
	int a0;		//指令数据切换线 低电平指令 高电平数据
	int cs;		//片选线	低电平有效
} pin_desc_t;

#define DEFAULT_MAJOR	0
#define USE_SEMAPHORE	1

typedef struct lcd_t {
	int dev_major;
	struct class *class;
	struct cdev *cdev;
	struct pin_desc_t pin;
	char buffer[162];
	unsigned int linepoint;
	int usedflag;
#if USE_SEMAPHORE
	struct semaphore sem;
#endif
} lcd_t;

static lcd_t *lcd = NULL;

static void begin_write_data(void)
{
	gpio_set_value(lcd->pin.cs, CS_ENABLE);
	gpio_set_value(lcd->pin.a0, A0_DATA);
	ndelay(200);
}

static void continue_write_data(unsigned char dat)
{
	int i;

	for (i = 0; i < 8; i++) {
		gpio_set_value(lcd->pin.sck, 0);	
		if ((dat & 0x80) == 0)
			gpio_set_value(lcd->pin.sda, 0);
		else
			gpio_set_value(lcd->pin.sda, 1);
		ndelay(10);
		gpio_set_value(lcd->pin.sck, 1);	
		dat <<= 1;
		ndelay(10);
	}
}

static void end_write_data(void)
{
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
	mdelay(200);

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
}

static void gpio_deconfig(void) {
	gpio_free(lcd->pin.sda);
	gpio_free(lcd->pin.sck);
	gpio_free(lcd->pin.a0);
	gpio_free(lcd->pin.rst);
	gpio_free(lcd->pin.cs);
}

static int lcd_open(struct inode *node, struct file *file)
{
	if (down_trylock(&lcd->sem)) {
		printk(KERN_ALERT "lcd is inuse!\n");
		return -EBUSY;
	}

	if (lcd->usedflag) {
		printk(KERN_INFO "lcd already in use!\n");
		up(&lcd->sem);
		return 0;
	}

	lcd->usedflag = 1;
	file->private_data = (void *)lcd;
	gpio_config(&lcd->pin);
	lcd_init();
	lcd_window_init( 0, 0, 53, 159);
	lcd_window_enable(true);
	lcd->linepoint = 0;

	up(&lcd->sem);
	return 0;
}

static int lcd_release(struct inode *node, struct file *file)
{
	lcd_t *p = (lcd_t *)file->private_data;
	if (down_trylock(&p->sem)) {
		return -EBUSY;
	}
	lcd_window_enable(false);
	file->private_data = NULL;
	gpio_deconfig();
	p->usedflag = 0;
	
	up(&p->sem);
	return 0;
}

#define LCD_DRV_MAGIC				'K'
#define LCD_CMD_MAKE(cmd)			(_IO(LCD_DRV_MAGIC, cmd))
#define LCD_IOCTL_CMD_GET(cmd)		(_IOC_NR(cmd))
#define LCD_IOCTL_CMD_IS_VALID(cmd)	((_IOC_TYPE(cmd) == LCD_DRV_MAGIC)?1:0)

#define LCD_WINDOW_START        3
#define LCD_WINDOW_CONTINUE     4
#define LCD_WINDOW_END			5
#define LCD_OPEN_SCREEN			6
#define LCD_CLOSE_SCREEN		7
#define LCD_RESET				99
#define LCD_INIT				100

static long lcd_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	int recvcmd;
	lcd_t *p = (lcd_t *)file->private_data;
	int i;
	int ret = 0;

	if (down_trylock(&p->sem)) {
		printk(KERN_ALERT "lcd is inuser!\n");
		return -EBUSY;
	}

	if (!LCD_IOCTL_CMD_IS_VALID(cmd)) {
		printk(KERN_ALERT "lcd_ioctl cmd magic error\n");
		up(&p->sem);
		return -EINVAL;
	}

	recvcmd = LCD_IOCTL_CMD_GET(cmd);
	
	switch(recvcmd) {
		case 1:
			printk(KERN_INFO "show pic!\n");
			break;
		case 2:
			printk(KERN_INFO "clear screen!\n");
			break;
		case LCD_WINDOW_START:
			write_cmd(0xa8 | (0 << 2) | (0 << 1) | (1 << 0));
			mdelay(15);
			begin_write_data();
			if ((unsigned int)arg > sizeof(p->buffer)) {
				printk(KERN_ALERT "line point too mush!it's should less 162\n");
				ret = -EINVAL;
			} else {
				p->linepoint = (int)arg;
			}
			break;
		case LCD_WINDOW_CONTINUE:
			if (copy_from_user(p->buffer, (unsigned char *)arg, p->linepoint)) {
				printk(KERN_ALERT "copy_from_user error\n");
				ret = -EFAULT;
				break;
			}
			if (p->linepoint == 0) {
				printk(KERN_ALERT "must set up linepoint value!\n");
				ret = -EINVAL;
				break;
			}
			//printk(KERN_INFO "LCD_WINDOW_CONTINUE: addr=%08x len=%d\n",  (unsigned char *)arg, p->linepoint);
			for (i = 0; i < p->linepoint; i++) {
				//write_data(buffer[i]);
				continue_write_data(p->buffer[i]);
			}
			break;
		case LCD_WINDOW_END:
			p->linepoint = 0;
			end_write_data();
			break;
		case LCD_OPEN_SCREEN:
			write_cmd(0xa8 | (0 << 2) | (0 << 1) | (1 << 0));
			mdelay(15);
			break;
		case LCD_CLOSE_SCREEN:
			write_cmd(0xa8 | (0 << 2) | (0 << 1) | (0 << 0));
			mdelay(15);
			break;
		case LCD_INIT:
			lcd_init();
			lcd_window_init( 0, 0, 53, 159);
			lcd_window_enable(true);
			break;
		case LCD_RESET:
			write_cmd(0xe2);
			mdelay(300);
			break;
		default:
			printk(KERN_ALERT "lcd_ioctl inval cmd:%d\n", recvcmd);
			ret = -EINVAL;
	}

	up(&p->sem);
	return ret;
}

static struct file_operations led_ops = {
	.owner = THIS_MODULE,
	.open = lcd_open,
	.release = lcd_release,
	//.read = lcd_read,
	//.write = lcd_write,
	.unlocked_ioctl = lcd_ioctl,
};

static int __init lcd_driver_init(void)
{
	int ret = 0;
	struct device *pdev;

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

	lcd->dev_major = register_chrdev(lcd->dev_major, "led_zy", &led_ops);
	if (lcd->dev_major < 0) {
		printk(KERN_ALERT "register chrdev failed\n");
		return ret;
	}
	
	lcd->usedflag = 0;

	sema_init(&lcd->sem, 1);
	printk(KERN_INFO "major = %d\n", lcd->dev_major);
	//CREATE DEVICE CLASS
	lcd->class = class_create(THIS_MODULE, "spilcd");	//对应/sys/class/spilcd
	if (IS_ERR(lcd->class)) {
		printk(KERN_ALERT "class create failed\n");
		unregister_chrdev(MKDEV(lcd->dev_major, 0), "led_zy");
		return PTR_ERR(lcd->class);
	}

	printk(KERN_INFO "devno=%d\n", MKDEV(lcd->dev_major, 0));
	pdev = device_create(lcd->class, NULL, MKDEV(lcd->dev_major, 0), NULL, "spilcd"); //对应/dev/spilcd
	if (IS_ERR(pdev)) {
		class_destroy(lcd->class);
		unregister_chrdev(MKDEV(lcd->dev_major, 0), "led_zy");
		printk(KERN_ALERT "device create failed\n");
		return PTR_ERR(pdev);
	}

	return 0;
}

static void __exit lcd_driver_exit(void)
{
	printk(KERN_DEBUG "lcd driver exit!!!\n");
	
	device_destroy(lcd->class, MKDEV(lcd->dev_major, 0));
	class_destroy(lcd->class);
	unregister_chrdev(MKDEV(lcd->dev_major, 0), "led_zy");

	kfree(lcd);
}

module_init(lcd_driver_init);
module_exit(lcd_driver_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("duanshuai");
MODULE_DESCRIPTION("linux kernel driver - lcd driver simulation spi");
MODULE_VERSION("0.1");
