#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/string.h>
#include <linux/platform_device.h>
#include <linux/ioport.h>
#include <linux/gpio.h>
#include <asm/io.h>
#include <asm/irq.h>

#include <mach/platform.h>
#include <mach/devices.h>

static struct resource s5p4418_led_resource[] = {
    [0] = {
        .name       = "led",
        .start      = GPIOC(1),
        .end        = GPIOC(1),
        .flags      = IORESOURCE_MEM, 
    },
};

static int s5p4418_led_release(struct device *dev)
{
    printk("--->device release\r\n");
    return 0;
}

static struct platform_device s5p4418_led_device = {
    .name       = "s5p4418-led",
    .id         = -1,
    .dev.release = s5p4418_led_release,
    .num_resources = ARRAY_SIZE(s5p4418_led_resource),
    .resource = s5p4418_led_resource,
};

static int __init s5p4418_led_init(void)
{
    int ret;
    printk("--->s5p4418_led_init\r\n");
    ret = platform_device_register(&s5p4418_led_device);
    if(ret)
    {
        platform_device_unregister(&s5p4418_led_device);
    }

    return ret;
}

static void __exit s5p4418_led_exit(void)
{
    printk("--->s5p4418_led_exit\r\n");
    platform_device_unregister(&s5p4418_led_device);
}

module_init(s5p4418_led_init);
module_exit(s5p4418_led_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("not me");
