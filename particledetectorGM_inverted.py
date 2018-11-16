from SimpleCV import *
import RPi.GPIO as GPIO
import time
import serial       #gps
import os           #to call a command in the terminal


def checkFix(buttgps,ledgps): # botton taking picture  
    gps = serial.Serial("/dev/ttyUSB0", baudrate = 9600) #start listening to the gps port
    GPIO.output(ledgps, GPIO.HIGH)                       # The red led stays high if gps doesnt find a fix if I dont press the button to start the program without fix
   
    while True:
        line = gps.readline()                            #reads the line from the usb port(gps)
        data = line.split(",")                           #parse the array, splitting with the commas of the line
       
        print ("Waiting for gpsfix, if you want to start without waiting for the fix press the Taking Picture Button")
        print("\n")
        if data[0] == "$GPGGA" and data[6] != "0":       #if the line i'm reading starts with $GPGGA and there is the fix==1,2
            print ("fix:")
            print("\n")
            print (data[6])
            GPIO.output(ledgps, GPIO.LOW)                # as soon it finds the fix the red led switches off
            return True
        input = GPIO.input(buttgps)
        if (input == False):                             # if the gps button is PRESSED
            print ("Buttongps is pressed")
                                                         #when the button is pressed the red led blinks 3 times
            for i in range(3):
                GPIO.output(ledgps, GPIO.LOW)            # led off
                time.sleep(0.5)
                GPIO.output(ledgps, GPIO.HIGH)           # led on
                time.sleep(0.5)
            GPIO.output(ledgps, GPIO.LOW)                # switches off the red led
            return True


def GPSdata(img_path,ledgps):
    gps = serial.Serial("/dev/ttyUSB0", baudrate = 9600)
    gcont= 0                            #to do the while only 1 time, one for the $GPGGA string and one for the $GPRMC string
    arrGPS = []                         #declare and empty list
    while gcont<1:
      line = gps.readline()             #reads the line from the usb port(gps)
      data = line.split(",")            #parse the array, splitting with the commas of the line
      if data[0] == "$GPRMC":           #if the line i'm reading starts with $GPRMC
          print("\n")
          print ("this is the gps GPRMC line " + line)
          print ("date", data[9])
          arrGPS.append(data[9])
          gcont = gcont + 1
  
    gcont = 0
    while gcont<1:
      line = gps.readline()             #reads the line from the usb port(gps)
      data = line.split(",")            #parse the array, splitting with the commas of the line
    
      if data[0] == "$GPGGA":           #if the line i'm reading starts with $GPGGA
          print("\n")
          print ("this is the gps GPGGA line " + line)
          print ("time utc", data[1])
          print ("latitude ", data[2] , data[3])
          print ("longitude", data[4] , data[5])
          print ("altitude (m)", data[9])
          print ("fix ", data[6])
          print ("satellites", data[7])
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

'''to be done later to adjust
def timeDifference(s1,s2,FMT): 
    tdelta = time.strptime(s2, FMT) - time.strptime(s1, FMT)
    return tdelta

'''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

button = 22                                     #this button is used both to stop the fix loading and to stop detecting particles
GPIO.setup(button,GPIO.IN, pull_up_down=GPIO.PUD_UP)
input = GPIO.input(button)

ledverde = 17
GPIO.setup(ledverde,GPIO.OUT)

ledrosso = 5
GPIO.setup(ledrosso,GPIO.OUT)

thresh_val=20
image_path= None
cont = 0                                        #particles
cicles = 0                                      #number of cicles of the while

'''---------------starting program-----------------------'''

print ("Running Program")
print("\n")
GPIO.output(ledverde, GPIO.HIGH)                # green led is always on 

if checkFix(button,ledrosso) is True:           #the program start after that the fix is set or after I decided to not wait for that
    time.ctime()                
    cam = Camera()
    display = Display()

    start = time.strftime('%H:%M:%S%p')         #starting time
    print("\n")
    print ("Starting Time:" + start)
    print("\n")
    print("When you want to stop the Detection Program press the Button\n")
    
    first = cam.getImage()                      #takes the first frame
    first_thresh = first.threshold(thresh_val)  #first threshold in RGB(0-255)
    while True:
      #cicles = cicles + 1
      #print(cicles)  
      #time.sleep(0.01) 
      tmp = cam.getImage() 
      tmp_thresh = tmp.threshold(thresh_val) 
      first_thresh = first_thresh + tmp_thresh      #every time update the first_thresh variable.
                                                    #It makes the sum of the new frame(tmp) with the one it has in memory
      '''first_thresh.show()                           #if you are in ssh mode you can comment this to be faster '''
      first_thresh_inverted = first_thresh.invert()
      first_thresh_inverted.show()
      
      input = GPIO.input(button)
      if (input == False):                           #if the gpio 22 is false//the button is PRESSED
                                                        #blink the green led 3 times/ each is half second
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
        '''first_thresh.show()                             #show the final frame with all the particles'''
        first_thresh_inverted.show()
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
            '''first_thresh.save(image_path)'''
            first_thresh_inverted.save(image_path)
          
                      
        else:
            #blobs.show(width=3) #this function shows you the detected blobs in greeen
            #time.sleep(10) 

            cont = str(blobs.count())                     # counts the number of blobs
            print("Detected Particles:" + cont)
            print("\n")
            image_path="%s-%s%s-%sparticles.jpg" % (start , stop , date , cont)
            first_thresh_inverted.save(image_path)


        gps_info = GPSdata(image_path, ledrosso)          #this fuction returns the array with gps informations

        #timelapse= timeDifference(start,stop,'%H:%M:%S%p')  #to be done
        #print (timelapse)
        
        updateLogfile(gps_info,start,stop,cont,image_path)


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

