from SimpleCV import *
import RPi.GPIO as GPIO
import time
import serial       #gps
import os           #to call a command in the terminal
import Adafruit_BMP.BMP085 as BMP085 #To control the temperature + pressure sensor
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306     # to control the display screen
import Image
import ImageDraw
import ImageFont

def checkFix(buttgps,ledgps): # button taking picture  
    gps = serial.Serial("/dev/ttyS0", baudrate = 9600) #start listening to the gps port
    GPIO.output(ledgps, GPIO.HIGH)                       # The red led stays high untill gps doesnt find a fix or I dont press the button to start the program without fix
   
    while True:
        line = gps.readline()                            #reads the line from the usb port(gps)
        data = line.split(",")                           #parse the array, splitting with the commas of the line
       
        print ("Waiting for GPS Fix, if you want to start without waiting, press the switch button !")
        print("\n")
        if data[0] == "$GPGGA" and data[6] != "0":       #if the line i'm reading starts with $GPGGA and there is the fix==1,2
            print ("Fix found : " + data[6])
            print("\n")
            GPIO.output(ledgps, GPIO.LOW)                # as soon it finds the fix the red led switches off
            return True
        input = GPIO.input(buttgps)
        if (input == False):                             # if the gps button is PRESSED
            for i in range(1):
                GPIO.output(buzzer, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(buzzer, GPIO.LOW)
                time.sleep(0.2)
                
            print ("Switch button is pressed")
                                                         #when the button is pressed the red led blinks 3 times
            for i in range(3):
                GPIO.output(ledgps, GPIO.LOW)            # led off
                time.sleep(0.5)
                GPIO.output(ledgps, GPIO.HIGH)           # led on
                time.sleep(0.5)
            GPIO.output(ledgps, GPIO.LOW)                # switches off the red led
            return True

def GPSdata(img_path,ledgps):
    gps = serial.Serial("/dev/ttyS0", baudrate = 9600)
    gcont= 0                            #to do the while only 1 time, one for the $GPGGA string and one for the $GPRMC string
    arrGPS = []                         #declare and empty list
    while gcont<1:
      line = gps.readline()             #reads the line from the usb port(gps)
      data = line.split(",")            #parse the array, splitting with the commas of the line
      if data[0] == "$GPRMC":           #if the line i'm reading starts with $GPRMC
          print("\n")
          print ("This is the GPS GPRMC line " + line)
          print ("date", data[9])
          arrGPS.append(data[9])
          gcont = gcont + 1  
    gcont = 0
    while gcont<1:
      line = gps.readline()             #reads the line from the usb port(gps)
      data = line.split(",")            #parse the array, splitting with the commas of the line
    
      if data[0] == "$GPGGA":           #if the line i'm reading starts with $GPGGA
          print("\n")
          print ("This is the GPS GPGGA line " + line)
          print ("Time UTC : ", data[1])
          print ("Latitude : " , data[2] , data[3])
          print ("Longitude : ", data[4] , data[5])
          print ("Altitude (m) : ", data[9])
          print ("Fix : ", data[6])
          print ("Satellites : ", data[7])
          print("\n")
          
          arrGPS.append(data[1])        #array where I save the gpsdata for the logfile later
          arrGPS.append(data[2])
          arrGPS.append(data[3])
          arrGPS.append(data[4])
          arrGPS.append(data[5])
          arrGPS.append(data[9])
          arrGPS.append(data[6])
          arrGPS.append(data[7])

          #modify exif data
          lat=data[2]
          long=data[4]
          alt=data[9]
          print("\n")
          print ("_______EXIFTOOL MESSAGE:")
          os.system('exiftool  -GPSLatitude="%s" -GPSLongitude="%s" -GPSAltitude="%s" "%s"' % (lat, long, alt, img_path))
          print("\n")
          print ("_______EXIF DATA OF THE FINAL FRAME:")
          os.system('exiftool "%s" ' %img_path)   #print the exifdata of the image
          print("\n")

          gcont = gcont + 1
          
          if data[6]=="0":
              GPIO.output(ledgps, GPIO.HIGH)      #led on tell you that it is not saving gps data because there is no fix        
    return arrGPS

def updateLogfile(arrGPS,start,stop,cont,path_img):
    path = './logGPS.csv'                   #path of the log file, if doesn't exist it is created now
    try:
        if os.stat(path).st_size > 0:       #if it exists not empty
           log_file = open(path,'a+')       #to open the file, a+: to modify without remove the previuos content
           print ("log file not empty")
        else:                               #if it exists empty
           log_file = open(path,'a+')       #to open the file, a+: to modify without remove the previuos content
           log_file.write('DATE;TIMEgps;LATITUDE;LONGITUDE;ALTITUDE;FIX;SATELLITES;STARTTIME;STOPTIME;NUMPARTICLES;PATH\n') #tab header 
           print ("empty logfile")
    except OSError:                         #if it doesnt exist or other issues
        log_file = open(path,'a+')          #create it and open it
        log_file.write('DATE;TIMEgps;LATITUDE;LONGITUDE;ALTITUDE;FIX;SATELLITES;STARTTIME;STOPTIME;NUMPARTICLES;PATH\n') #tab header
        print ("no file, creating new file")
            
    #upload the logfile
    log_file.write(arrGPS[0])
    log_file.write(';')
    log_file.write(arrGPS[1])
    log_file.write(';')
    log_file.write(arrGPS[2])
    log_file.write(arrGPS[3])
    log_file.write(';')
    log_file.write(arrGPS[4])
    log_file.write(arrGPS[5])
    log_file.write(';')
    log_file.write(arrGPS[6])
    log_file.write(';')
    log_file.write(arrGPS[7])
    log_file.write(';')
    log_file.write(arrGPS[8])
    log_file.write(';')
    log_file.write(start)
    log_file.write(';')
    log_file.write(stop)
    log_file.write(';')
    log_file.write(cont)
    log_file.write(';')
    log_file.write(path_img)
    log_file.write('\n')      #new line in the logfile      
    log_file.close()          #close the logfile

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

button = 22                                     #this button is used both to stop the fix loading and to stop detecting particles
GPIO.setup(button,GPIO.IN, pull_up_down=GPIO.PUD_UP)
input = GPIO.input(button)

ledverde = 17                   # To control the green led
GPIO.setup(ledverde,GPIO.OUT)

ledrosso = 5                    # To control the red led
GPIO.setup(ledrosso,GPIO.OUT)

buzzer = 25                     # To control the buzzer
GPIO.setup(buzzer, GPIO.OUT)

RST = 24                        # To control the display screen

thresh_val=20                   #Value of the threshold
image_path= None
cont=0                                          #particles
cicles = 0                                      #number of cicles of the while

'''---------------starting program-----------------------'''

#----------Initialization of the display screen------------ 


disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)             # Read the pin on which the screen is connected, here pin 24

# Initialize library.
disp.begin()
# Clear display.
disp.clear()
disp.display()
# Create blank image for drawing.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
# First define some constants to allow easy resizing of shapes.
padding = 2
shape_width = 80
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = padding
font = ImageFont.load_default()                 # We use the default font on the screen

print ("Running Program")
print("\n")
GPIO.output(ledverde, GPIO.HIGH)                # green led is always on 

if checkFix(button,ledrosso) is True:           # The program starts after the fix is set or after I decided to not wait for that
    time.ctime()                
    Cam = Camera()
    display = Display()

    start = time.strftime('%H:%M:%S%p')         #starting time
    print("\n")
    print ("Starting Time:" + start)
    print("\n")
    print("When you want to stop the Detection Program press the Button\n") #Display in the Terminal
    print ('Number of particles detected in real time : ')
    print("\n")
  
    sensor = BMP085.BMP085()                    # call the function which allows you to use the BMP180 sensor
    print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))       #Function which displays the temperature at the  beginning of the experiment
    print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()))      # Same thing with the pressure             
    print("\n")   
    
    first = Cam.getImage()                      #takes the first frame
    first_thresh = first.threshold(thresh_val)  #first threshold in RGB(0-255)
    
    while True:
      #cicles = cicles + 1
      #print(cicles)  
      #time.sleep(0.01) 
      tmp = Cam.getImage() 
      tmp_thresh = tmp.threshold(thresh_val) 
      first_thresh = first_thresh + tmp_thresh      #every time update the first_thresh variable.
                                                    #It makes the sum of the new frame(tmp) with the one it has in memory
    
      particle = tmp_thresh.findBlobs(minsize=1)    # Find the latest particle(s) on the image
      blobs = first_thresh.findBlobs(minsize=1)     # Find all the particles detected from the beginning 
      first_thresh.show()                           #if you are in ssh mode you can comment this to be faster
      time.sleep(0)           
      
      if particle is None:                          # If no new particle on the latest image,
         GPIO.output(buzzer, GPIO.LOW)              # Then the buzzer won't beep.
         counter = str(0)         
      else:          
          counter= str(particle.count())            # count the number of particles detected when the buzzer beeps 
          count= int(counter)
          total = str(blobs.count())                # return the sum of particles detected in real time
          tot = int(total)
          date= time.strftime('%a, %d %b %Y, %H:%M:%S%p') #Return the date and time          
          
          for i in range (1):                       # Else, the buzzer will beep once when a new particle is detected.
              GPIO.output(buzzer, GPIO.HIGH)
              time.sleep(0.5)
              GPIO.output(buzzer, GPIO.LOW)
              time.sleep(0.5)
              
              # Display the number of particles in real time on the display screen
              disp.clear()                          #Clear the display
              disp.display()                        
              image = Image.new('1', (width, height))   # create a new image on the display
              draw = ImageDraw.Draw(image)
              draw.rectangle((0,0,width,height), outline=0, fill=0)     #Draw this image with a black backgroung          
              draw.text((x, top),' Events : '+ total, font=font, fill=255)     # Write the number of particles detected in real time       
              draw.text((x, top+10),' Pressure: {0:0.0f}'.format(sensor.read_pressure()), font=font, fill=255)    #Write the pressure in Pascal
              draw.text((x+100, top+10), ' Pa', font=font, fill=255)                 
              draw.text((x, top+20), ' Temperature: {0:0.2f}'.format(sensor.read_temperature()), font=font, fill=255) # Write the temperature in Celsius
              draw.text((x+110, top+20), ' *C', font=font, fill=255)
              disp.image(image)                                         # Display the temperature
              disp.display()
              
              print("  - - - - - - - - - - - - -  ")
              print("\n")
                         
              if (tot == 1):                             #Special loop just for 1 particle               
                  print(" You detected 1 particle.")
                  print("\n")                             
                  print('Date = ' + date)                   #print the date and time of the event                  
                  print('Temp = {0:0.2f} *C'.format(sensor.read_temperature())) #print the temperature of the event
                  print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure())) # print the pressure of the event
                  print("\n")
                  
              else:                                             # if you detect more particles                                   
                  print (" You detected " + total + " particles.") # print the number of particles detected in real time
                  print("\n")               
                  print('Date = ' + date)                        #print the date ant time of the event                                
                  print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))     #temperature
                  print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()))    #pressure
                  print("\n")
              break
                                
      input = GPIO.input(button)
      if (input == False):                           #if the gpio 22 is false//the button is PRESSED, used to stop the detection
        print ("\n")                                                #blink the green led 3 times/ each is half second
        print(" - - - - Detection stopped, end of the program - - - - ")
        print("\n")
        
        for i in range(2):
            GPIO.output(buzzer, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(buzzer, GPIO.LOW)
            time.sleep(0.2)
        for i in range(3):
            GPIO.output(ledverde, GPIO.LOW)             # led off
            time.sleep(0.5)
            GPIO.output(ledverde, GPIO.HIGH)            # led on
            time.sleep(0.5)                    
        stop = time.strftime('%H:%M:%S%p')              #time of stop
        date = time.strftime(' on %b %d %Y')    
        print ("Detection stop time:" + stop)
        print("\n")
        print ("Taking Picture..")
        print("\n")
        first_thresh.show()                             #show the final frame with all the particles
        time.sleep(3)
        print ("Counting particles..")
        #print (cicles)
        print("\n")
        
        blobs = first_thresh.findBlobs(minsize=1)       #set the lower value of the size of the blob
      
        if blobs is None:                               #if the are no blobs
            for i in range(5):
                GPIO.output(ledrosso, GPIO.HIGH)        # led on
                time.sleep(0.5)
                GPIO.output(ledrosso, GPIO.LOW)         # led off
                time.sleep(0.5)
            cont = str(0)
            print ("No detected particles!")
            print("\n")
            image_path="%s-%s%s-%sparticles.jpg" % (start , stop , date ,  cont)
            first_thresh.save(image_path)      
                      
        else:
            cont = str(blobs.count())                     # counts the number of blobs
            print("Detected Particles:" + cont)
            print("\n")
            image_path="%s-%s%s-%sparticles.jpg" % (start , stop , date , cont)
            first_thresh.save(image_path)

        gps_info = GPSdata(image_path, ledrosso)                #this fuction returns the array with gps informations
        updateLogfile(gps_info,start,stop,cont,image_path)      # Save the data in a file

        #to see if the stopping button is pressed the green led blinks 3 times
        for i in range(3):
            GPIO.output(ledverde, GPIO.LOW)               # led off
            time.sleep(0.5)
            GPIO.output(ledverde, GPIO.HIGH)              # led on
            time.sleep(0.5)
          
            
        GPIO.output(ledrosso, GPIO.LOW)                   # switches of the red led
        GPIO.output(ledverde, GPIO.LOW)                   #switches of the green led
        time.sleep(2)
        break
        
    GPIO.cleanup()
