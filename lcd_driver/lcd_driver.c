#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>


typedef struct gpio_reg {
	int cfg0;
	int cfg1;
	int cfg2;
	int cfg3;
	int dat;
	int drv0;
	int drv1;
	int pul0;
	int pul1;
} gpio_reg;

struct gpio_dev {
	struct cdev cdev;
	char name[32];

} gpio_dev;

#define		MEMORY_BASE 0x1C200000
#define		PIO_OFFSET	0x800
#define		GPIO_OFFSET 0x24

static ssize_t drv_read(struct file* filp, char* buf, size_t count, loff_t* ppos) {
	printk("device read\n");
	return count;
}

static ssize_t drv_write(struct file* filp, const char* buf, size_t count, loff_t* ppos) {
	printk("device write\n");
	return count;
}

static int drv_open(struct inode* inode, struct file* filp) {
	printk("device open\n");

	gpio_reg *gpio = (gpio_reg *)ioremap(MEMORY_BASE + PIO_OFFSET, 1024);
	if (gpio == NULL) {
		printk("ioremap failed\n");
		perror(ioremap);
		return -1;
	}
	
	return 0;
}

static long drv_ioctl(struct file* filp, unsigned int cmd, unsigned long value) {
	printk("device ioctl\n");
	return 0;
}

static int drv_release(struct inode* inode, struct file* filp) {
	printk("device close\n");
	return 0;
}

struct file_operations drv_fops = {
	read:
		drv_read,
	write:
		drv_write,
	unlocked_ioctl:
		drv_ioctl,
	open:
		drv_open,
	release:
		drv_release,
};

#define MAJOR_NUM 60
#define MODULE_NAME "DEMO"

static int demo_init(void) {
	if (register_chrdev(MAJOR_NUM, "demo", &drv_fops) < 0) {
		printk("<1>%s: can't get major %d\n", MODULE_NAME, MAJOR_NUM);
		return (-EBUSY);
	}

	printk("<1>%s: started\n", MODULE_NAME);
	return 0;
}

static void demo_exit(void) {
	unregister_chrdev(MAJOR_NUM, "demo");
	printk("<1>%s: removed\n", MODULE_NAME);
}

module_init(demo_init);
module_exit(demo_exit);
