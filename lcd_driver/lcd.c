

//LCM resolution:320x160 ;
//driver IC:UC1698u,B/W, 8080Mode 8bit;
//ccwu 2008-01-16;
#include <REG52.H>
//#include "uc1698u.h"
//#include "uc1698u_1.h"
//#include "uc1698u_2.h"
//#include "uc1698u_3.h"
//#include "uc1698u_4.h"

sbit CS0 = P3^6;
sbit CD  = P3^0;		
sbit WR1 = P3^5;
sbit WR0 = P3^4;	   
sbit RST = P3^7;
sbit SCLK= P1^0;
sbit SDA=  P1^1;
sbit step = P3^2;


void writei(unsigned char ins);
void writed(unsigned char dat); 

void display_map2(void);
unsigned char code map2[];

void display_map1(void);
unsigned char code map1[];

void display_map(unsigned char *pic);
void delay(long tt); 
void display_black(void);
void display_white(void);
void vertical(void);
void horizontal(void);
void snow();
void frame();
void window_program(void);
void lcd_initial(void);
void press(void);
void dispaly_pic();
void network();
unsigned char read_data();
unsigned char read();

void main(void)
{

	CS0=0;

	RST=0;
	delay(2000);
	RST=1;
	delay(2000);

	RST=0;
	delay(2000);
	RST=1;
	delay(2000);

	lcd_initial(); 
	delay(2000);
	//display_white();
	//read();
	//read_data();
	//press(); 
	while(1)   
	{
		display_map2();
		delay(2000);
		press(); 

		display_map1();
		delay(2000);
		press(); 

		display_black();
		delay(2000);
		press(); 
		display_white();
		delay(2000);
		press(); 

		vertical(); 
		delay(2000);
		press(); 

		horizontal();     
		delay(2000);
		press(); 

		snow();
		delay(2000);
		press(); 

		// network();
		// delay(2000);
		// press(); 

		//frame();
		//delay(2000);


		// display_map(map3);
		// delay(2000);
		// press();


		//display_map(map4);
		//delay(2000);
		//press();
	}
}

unsigned char read()
{
	unsigned char status1;
	//unsigned char status2,status3,status4,status5;
	////¼ÇµÃÏÈÉèÖÃÒª¶ÁµÄµØÖ·£¬Èç¹ûÔÚ¿Õ¶ÁÒ»´ÎÔÙÉèÖÃµØÖ·µÄ»°¾Í»á×óÒ»¸ö8bit
	//writei(0x10);  
	//writei(0x00);  
	//writei(0x60);
	//writei(0x70); 
	////////¿Õ¶Á//////////////
	CS0=0;
	WR0=1;
	P1=0xff; 
	CD=1;

	WR1=0;
	status1=P1;
	WR1=1;
	//P1=status1;
	/*
	/////////¶ÁµÚ1¸ö8bit////////
	CS0=0;
	WR0=1;
	P1=0xff; 
	CD=1;

	WR1=0;
	status2=P1;
	WR1=1;
	P1=status2;
	/////////¶ÁµÚ2¸ö8bit////////
	CS0=0;
	WR0=1;
	P1=0xff;
	CD=1;

	WR1=0;
	status3=P1;
	WR1=1;
	P1=status3;

	CS0=1;
	/////////¶ÁµÚ4¸ö8bit//////// 
	CS0=0;
	WR0=1;
	P1=0xff;
	CD=1;

	WR1=0;
	status5=P1;
	WR1=1;
	P1=status5;
	 */
	CS0=1;
	return(status1);

}

unsigned char read_data()
{
	int i;
	unsigned char temp0,temp1,temp2,temp3,data_r,data_g,data_b;
	unsigned char data0,data1,data2;

	for(i=0;i<30;i++)
	{
		writei(0x00);//set column
		writei(0x10);
		writei(0x60|i);//set row 
		writei(0x70);

		writed(0xf0); 
		writed(0xf0); 
		writed(0xf0);

		writei(0x00);//set column
		writei(0x10);
		writei(0x60|i);//set row 
		writei(0x70);

		read();//dummy 
		temp0=read();
		temp1=read();
		temp2=read();
		temp3=read();
		//////////565 change 444//////////////////////////
		data_r=temp0&0xf0;
		data_g=((temp0&0x07)<<1)|((temp1&0x80)>>7);
		data0=data_r|data_g;

		data_b=((temp1&0x1f)>>1);
		data_r=temp2&0xf0;
		data1=(data_b<<4)|(data_r>>4);

		data_g=((temp2&0x07)<<1)|((temp3&0x80)>>7);
		data_b=((temp3&0x1f)>>1);
		data2=((data_g<<4)|(data_b));
		//////////////////////////////////////////////////

		writei(0x00);//set column
		writei(0x10);
		writei(0x60|i);//set row 
		writei(0x72);

		writed(data0); 
		writed(data1); 
		writed(data2);

	}  
}

void lcd_initial()
{
	writei(0xe2); // set system reset

	delay(2000);  //delay 200ms

	writei(0x24); //set Temp. command  TC1TC0 00=-0.00%
	writei(0x2b); //internal pump
	writei(0xC0); //set lcd mapping  MY=0,Mx=0,LC0=0

	writei(0xA2); //set line rate
	writei(0xc8);//set n-line
	writei(0x0f);

	//writei(0xf1);
	//writei(79);

	writei(0xD1); //set color pattern RGB

	writei(0xD5); //set 4K color mode

	writei(0xE9); //set lcd bias ratio: 1/10bias

	writei(0x81); //set Vbias potentiometer
	writei(188);  //set contrast level:0-255      

	// writei(0xde); //set com scan function

	//writei(0x31);  //apc
	//writei(0xed);  // 

	writei(0xA9); //display enable    

}

void window_program(void)      //set window
{
	writei(0x05);//set column
	writei(0x12);
	writei(0x60);//set row 
	writei(0x70);

	writei(0xF4); //set start column 
	writei(0x25); //start seg1

	writei(0xF5); //set start row
	writei(0x00);  // start com1

	writei(0xF6);  //set end column
	writei(0x5a);  // end seg320  

	writei(0xF7);  //set end row
	writei(0x9F);  //end com160
}

void display_black(void)
{
	int i;
	int j;
	window_program();
	for(i=0;i<160;i++)
	{

		for(j=0;j<54;j++)
		{
			writed(0xff); 
			writed(0xff); 
			writed(0xff);
		}
	}


}

void display_white(void)
{
	int i;
	int j;
	window_program();
	for(i=0;i<160;i++)
	{

		for(j=0;j<54;j++)
		{
			writed(0x00); 
			writed(0x00); 
			writed(0x00);
		}
	}
}

void snow()
{
	int i;
	int j;
	window_program();
	for(i=0;i<80;i++)
	{
		for(j=0;j<81;j++)
		{
			writed(0xf0); 
			//writed(0xf0);
			// writed(0xf0);
		}
		for(j=0;j<81;j++)
		{
			writed(0x0f);
			// writed(0x0f);
			// writed(0x0f);
		}

	}
}

void network()
{
	int i;
	int j;
	window_program();
	for(i=0;i<160;i++)
	{
		for(j=0;j<54;j++)
		{
			writed(0xf0); 
			writed(0xf0);
			writed(0xf0);
		}
		for(j=0;j<54;j++)
		{
			writed(0xff);
			writed(0xff);
			writed(0xff);
		}

	}
}


void horizontal()
{  
	int i;
	int j;
	window_program();

	for(i=0;i<80;i++)
	{
		for(j=0;j<81;j++)
		{
			writed(0xff); 
			//  writed(0xff); 
			// writed(0xff);
		}

		for(j=0;j<81;j++)
		{
			writed(0x00); 
			//    writed(0x00); 
			//	   writed(0x00);
		}
	}


}

void vertical()
{
	int i;
	int j;
	window_program();
	for(i=0;i<160;i++)
	{
		for(j=0;j<54;j++)
		{
			writed(0xf0); 
			writed(0xf0); 
			writed(0xf0);
		}
	}
}

void frame()
{
	int i,j;
	window_program();  
	for(i=0;i<160;i++)
	{
		if(i==0||i==159)
		{
			for(j=0;j<54;j++)
			{writed(0xff); 
				writed(0xff); 
				writed(0xff);} 
		}
		else
			for(j=0;j<54;j++)
			{
				if(j==0)
				{writed(0xf0);
					writed(0x00);
					writed(0x00);}
				else if(j==53)
				{writed(0x0f);
					writed(0x00);
					writed(0x00);}
				else
				{
					writed(0x00); 
					writed(0x00); 
					writed(0x00);	
				}
			}
	}
}
void display_map2(void)
{    int k=0;
	int i,j;
	window_program();
	// writei(0x70);  //set COM start address H
	// writei(0x60);  //                      L
	// writei(0x12); //set SEG  start address  H
	// writei(0x05); //                        L


	for(i=0;i<80;i++)
	{
		for(j=0;j<162;j++)
		{
			writed(map2[k++]);
		}
	}
}
void display_map1(void)
{    int k=0;
	int i,j;
	window_program();
	// writei(0x70);  //set COM start address H
	// writei(0x60);  //                      L
	// writei(0x12); //set SEG  start address  H
	// writei(0x05); //                        L


	for(i=0;i<80;i++)
	{
		for(j=0;j<162;j++)
		{
			writed(map1[k++]);
		}
	}
}
/*
   void display_map(unsigned char *pic)
   {
   int i,j,k=0;

   writei(0x00);//set column 1
   writei(0x10);
   writei(0x60);//set row 1
   writei(0x70);

   writei(0xF4); //set start column 1
   writei(0x25); //start seg 1

   writei(0xF5); //set start row 1
   writei(0x00);  // start com 1

   writei(0xF6);  //set end column
   writei(0x5a);  // end seg240

   writei(0xF7);  //set end row
   writei(159);  //end com120

   writei(0xf8);  //enable

   for (i=0;i<120;i++)
   {
   for(j=0;j<120;j++)
   {				
   writed(pic[k++]);
   }
   }



   }
 */

/*
   void dispaly_pic()
   {
   int k=0;      
   int i,j;

   unsigned char temp,temp1,temp2,temp3,temp4,temp5,temp6,temp7,temp8;
   unsigned char h11,h12,h13,h14,h15,h16,h17,h18,d1,d2,d3,d4;

   writei(0x00);//set column
   writei(0x10);
   writei(0x60);//set row 
   writei(0x70);

   writei(0xF4); //set start column 
   writei(0x00); //start seg1

   writei(0xF5); //set start row
   writei(0x00);  // start com1

   writei(0xF6);  //set end column
   writei(0x6a);  // end seg320

   writei(0xF7);  //set end row
   writei(0x9F);  //end com160

   for(i=0;i<160;i++)           //240*128 B/W picture for example
   {
   for(j=0;j<40;j++)        //240 dot/ 8 bite=30 byte.
   {                        //Function:1STEP..read 8bit byte's bit data'bit(bit7~0)'s value; 
//2STEP.. change the data format to the DR's data format(B/W display==>
//16Gray display);
//3STEP..write data to DDRAM.
temp=pic[k++];        //1:turns 1byte B/W data to 4k-color data(RRRR-GGGG-BBBB)
temp1=temp&0x80;      //&1000,LSB==>MSB BIT( move to MSB'high byte.)
temp2=(temp&0x40)>>3; //&0100,LSB          ( move to LSB'high byte.)
temp3=(temp&0x20)<<2; //&0010,LSB==>keep the 8byte's 3'nd's value.
temp4=(temp&0x10)>>1; //&0001,LSB==>read 8bit byte's 4'rd's value.
temp5=(temp&0x08)<<4; //&MSB,1000
temp6=(temp&0x04)<<1; //&MSB,0100          
temp7=(temp&0x02)<<6; //&MSB,0010==>example:if temp=1000,0011==>temp7=1000,0000
temp8=(temp&0x01)<<3; //&MSB,0001==>example:if temp=1000,0011==>temp8=0000,1000
h11=temp1|temp1>>1|temp1>>2|temp1>>3;  //2:data format change:from B/W==>16 GRAY
h12=temp2|temp2>>1|temp2>>2|temp2>>3;
h13=temp3|temp3>>1|temp3>>2|temp3>>3;
h14=temp4|temp4>>1|temp4>>2|temp4>>3;
h15=temp5|temp5>>1|temp5>>2|temp5>>3;  
h16=temp6|temp6>>1|temp6>>2|temp6>>3;
h17=temp7|temp7>>1|temp7>>2|temp7>>3;  //example:if temp7=1000,0000==>h17=1111,0000
h18=temp8|temp8>>1|temp8>>2|temp8>>3;  //example:if temp8=0000,1000==>h18=0000,1111
d1=h11|h12;                            //3:1 byte=(1MSB+1LSB)/per 2 pixel=2dot. 
d2=h13|h14;                            //the DR's 4bit=1dot==>8bit=2dot display.
d3=h15|h16;                            
d4=h17|h18;                            //example:if h17=1111,0000 h18=0000,1111==>d4=1111,1111
writed(d1);                            //4:write data to DDRAM:data format=4k color mode.
writed(d2);                            //(Note:the DR of UC1698U need 4 times send)..P23.
writed(d3);
writed(d4);
}

}

}
 */
void writei(unsigned char ins)
{
	//   CS0=0;
	//	CD=0;
	//	WR1=1;	

	//    P1=ins; 
	//    WR0=0;			  
	//		WR0=1;    
	//      CS0=1;  

	int i;
	CS0=0;
	CD=0;
	for(i=0;i<8;i++)
	{
		SCLK=0;
		if((ins&0x80)==0)
			SDA=0;
		else
			SDA=1;
		SCLK=1;
		ins=ins<<1;
	}               
}

void writed(unsigned char dat)
{
	//    CS0=0;
	//		CD=1; 
	//	    WR1=1;	  

	//		P1=dat; 
	//		WR0=0;       
	//		WR0=1;    
	//      CS0=1;  

	int i;
	CS0=0;
	CD=1;
	for(i=0;i<8;i++)
	{
		SCLK=0;
		if((dat&0x80)==0)
			SDA=0;
		else
			SDA=1;
		SCLK=1;
		dat=dat<<1;
	}
}

void delay(long tt)
{
	while(tt>0){
		tt--;
	}
}

void press(void)
{
	while(step);
}

