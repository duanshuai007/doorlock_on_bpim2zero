#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/errno.h>
#include <linux/device.h>
#include <linux/cdev.h>
#include <linux/platform_device.h>
#include <linux/io.h>
#include <linux/gpio.h>
#include <linux/pm.h>

#include <mach/platform.h>
#include <mach/devices.h>
#include <mach/soc.h>

static int dev_major = -1;

static struct leds{
    int pins;
    char *names;
}leds;

static struct s5p4418_led {
    struct cdev     *cdev;
    struct class    *class;
    int             openflag;
}s5p4418_led;

static int led_open(struct inode *inode, struct file *filp)
{
    printk("--->led_open\r\n");
    gpio_request(leds.pins, "led");
    gpio_direction_output(leds.pins, 1);
    return 0;
}

static int led_release(struct inode *inode, struct file *filp)
{
    printk("--->led_close\r\n");
    gpio_free(leds.pins);
    return 0;
}

static long led_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    printk("--->led_ioctl\r\n");
    unsigned int ops;
    ops = _IOC_NR(cmd);
    if((ops != 0) && (ops != 1))
    {
        return -EINVAL;
    }
    switch(ops)
    {
        case 0:
            gpio_set_value(leds.pins, 0);
            break;
        case 1:
            gpio_set_value(leds.pins, 1);
            break;
        default:
            return -EINVAL;
    }

    return 0;
}

static struct file_operations s5p4418_led_ops = {
    .owner      = THIS_MODULE,
    .open       = led_open,
    .release    = led_release,
    .unlocked_ioctl = led_ioctl,
};

static int led_probe(struct platform_device *dev)
{
    int ret;
    struct resource *led_resource;
    struct platform_device *pdev = dev;
    dev_t devno;

    printk("match ok!\r\n");

    if(dev_major > 0)
    {
        devno = MKDEV(dev_major, 0);
        ret = register_chrdev_region(devno, 1, "s5p4418-led");
    }else
    {
        ret = alloc_chrdev_region(&devno, 0, 1, "s5p4418-led");
        dev_major = MAJOR(devno);
    }

    if(ret < 0)
        return ret;

    s5p4418_led.class = class_create(THIS_MODULE, "s5p4418-led");
    s5p4418_led.cdev = cdev_alloc();
    cdev_init(s5p4418_led.cdev, &s5p4418_led_ops);
    ret = cdev_add(s5p4418_led.cdev, devno, 1);
    if(ret)
    {
        printk("add device failed\r\n");
        return ret;
    }
    printk("led cdev:%08x\r\n", &s5p4418_led.cdev);

    device_create(s5p4418_led.class, NULL, devno, NULL, "s5p4418-led");

    led_resource = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    if(led_resource == NULL)
        return -ENOENT;
    leds.pins = led_resource->start;
    leds.names = led_resource->name;

    printk("pin=%d,name=%s\r\n", leds.pins, leds.names);

    return 0;
}

static int led_remove(struct platform_device *pdev)
{
    device_destroy(s5p4418_led.class, MKDEV(dev_major, 0));
    cdev_del(s5p4418_led.cdev);
    class_destroy(s5p4418_led.class);

    unregister_chrdev_region(MKDEV(dev_major, 0), 1);

    return 0;
}

static struct platform_driver led_driver = {
    .probe      = led_probe,
    .remove     = led_remove,
    .driver = {
        .name   = "s5p4418-led",
        .owner  = THIS_MODULE,
    },
};

static int __init platform_driver_init(void)
{
    int ret;

    ret = platform_driver_register(&led_driver);
    if(ret)
    {
        printk("--->platform_driver_register failed\r\n");
        platform_driver_unregister(&led_driver);
    }

    return ret;
}

static void __exit platform_driver_exit(void)
{
    printk("--->platform_driver_exit\r\n");
    platform_driver_unregister(&led_driver);
}

module_init(platform_driver_init);
module_exit(platform_driver_exit);

MODULE_LICENSE("GPL");
