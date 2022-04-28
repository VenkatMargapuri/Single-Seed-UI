# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 09:46:46 2016

Sample for tisgrabber to OpenCV Sample 2

Open a camera by name
Set a video format hard coded (not recommended, but some peoples insist on this)
Set properties exposure, gain, whitebalance
"""
import ctypes as C
import tisgrabber as IC
import cv2
import numpy as np
import serial
import time
import sys
import PySimpleGUI as sg
import os
import demo_carving
import datetime
import csv
from os import path
from CalculateVolume import CalculateVolume


def FindCamera():
    # Create the camera object.
    Camera = IC.TIS_CAM()

    # List availabe devices as uniqe names. This is a combination of camera name and serial number
    Devices = Camera.GetDevices()
    for i in range(len( Devices )):
        print( str(i) + " : " + str(Devices[i]))

    # Open a device with hard coded unique name:
    Camera.open('DFK 37BUX287 15910398')
    # or show the IC Imaging Control device page:

    #Camera.ShowDeviceSelectionDialog()
    
    return Camera

def SetCamera(camera):
    if camera.IsDevValid() == 1:
        #cv2.namedWindow('Window', cv2.cv.CV_WINDOW_NORMAL)
        print( 'Press ctrl-c to stop' )

        # # Set a video format
        #camera.SetVideoFormat("RGB32 (640x480)")
        
        # #Set a frame rate of 30 frames per second
        camera.SetFrameRate( 30.0 )
        
        # # Start the live video stream, but show no own live video window. We will use OpenCV for this.
        camera.StartLive(1)    

        # Set some properties
        # Exposure time

        ExposureAuto=[1]
        
        camera.GetPropertySwitch("Exposure","Auto",ExposureAuto)
        print("Exposure auto : ", ExposureAuto[0])

        
        # In order to set a fixed exposure time, the Exposure Automatic must be disabled first.
        # Using the IC Imaging Control VCD Property Inspector, we know, the item is "Exposure", the
        # element is "Auto" and the interface is "Switch". Therefore we use for disabling:
        #camera.SetPropertySwitch("Exposure","Auto",0)
        # "0" is off, "1" is on.

        ExposureTime=[0]
        camera.GetPropertyAbsoluteValue("Exposure","Value",ExposureTime)
        print("Exposure time abs: ", ExposureTime[0])

        
        # Set an absolute exposure time, given in fractions of seconds. 0.0303 is 1/30 second:
        camera.SetPropertyAbsoluteValue("Exposure","Value", 0.99)

        # # Proceed with Gain, since we have gain automatic, disable first. Then set values.
        Gainauto=[0]
        camera.GetPropertySwitch("Gain","Auto",Gainauto)
        print("Gain auto : ", Gainauto[0])
        
        camera.SetPropertySwitch("Gain","Auto",0)
        camera.SetPropertyValue("Gain","Value",25)

        WhiteBalanceAuto=[0]
        # Same goes with white balance. We make a complete red image:
        camera.SetPropertySwitch("WhiteBalance","Auto",0)
        camera.GetPropertySwitch("WhiteBalance","Auto",WhiteBalanceAuto)
        print("WB auto : ", WhiteBalanceAuto[0])

        camera.SetPropertySwitch("WhiteBalance","Auto",1)
        camera.GetPropertySwitch("WhiteBalance","Auto",WhiteBalanceAuto)
        print("WB auto : ", WhiteBalanceAuto[0])
        
        GammaAuto = [0]
        camera.SetPropertySwitch("Gamma", "Auto", 0)
        camera.GetPropertySwitch("Gamma", "Auto", GammaAuto)
        
        camera.SetPropertySwitch("Gamma", "Auto", 180)
        camera.GetPropertySwitch("Gamma", "Auto", GammaAuto)
        
        Brightness = [0]
        camera.SetPropertySwitch("Brightness", "Auto", 0)
        camera.GetPropertySwitch("Brightness", "Auto", Brightness)
        
        camera.SetPropertySwitch("Brightness", "Auto", 500)
        
        camera.SetPropertyValue("WhiteBalance","White Balance Red",255)
        camera.SetPropertyValue("WhiteBalance","White Balance Green",255)
        camera.SetPropertyValue("WhiteBalance","White Balance Blue",255)    
        
        time.sleep(10)
    #else:
        #print( "No device selected")
    
def CaptureImage(camera, count):
    try:
        # Snap an image
        camera.SnapImage()
        #Img number is one less than count
        imgNumber = count - 1
        # Get the image
        image = camera.GetImage()
        # Apply some OpenCV function on this image
        image = cv2.flip(image,0)
        #image = cv2.erode(image,np.ones((11, 11)))
        if(imgNumber >= 10):            
            cv2.imwrite("./00{}.bmp".format(imgNumber), image)
        else:
            cv2.imwrite("./000{}.bmp".format(imgNumber), image)
        #cv2.imshow('Window', image)
        #cv2.waitKey(10)
           
    except KeyboardInterrupt:
        camera.StopLive()    
        cv2.destroyWindow('Window')   

# Send the GCode command to the servo
def SendGCode(connection, turn):   
    print("Sending: " + turn)
    connection.write((turn + '\n').encode('utf-8'))
    grbl_out = connection.readline()
    print(grbl_out.strip())
    
# Creates a new folder if it doesn't exist. Else, creates a folder named default
# If the folder exists, the contents of the folder are cleared.    
def CreateFolderandChangeDir(dir):
    path = os.path.join(os.getcwd(), dir)
    if(not os.path.exists(path)):
        os.mkdir(path)

    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
    os.chdir(path)
    
# Moves to the parent of the current directory after the images are done being captured.    
def ReverttoParentDir():
    os.chdir('../')
    
def CreateCSVFile(researcher, location, description, imageCount, rotation, filename, dateTime, volume):
    fields = ['Date-Time', 'Researcher', 'Location', 'Description', 'Image Count', 'Rotation (in degrees)', 'length', 'width', 'height', 'Volume']
    values = [dateTime, researcher, location, description, imageCount, rotation, volume]
    try:
        if(path.exists(filename + '.csv')):            
            with open(filename + '.csv', 'a', newline='') as csvFile:
                csvWriter = csv.writer(csvFile)        
                csvWriter.writerow(values)
        else:
            with open(filename + '.csv', 'w+', newline='') as csvFile:
                csvWriter = csv.writer(csvFile)                
                csvWriter.writerow(fields)
                csvWriter.writerow(values)
    except Exception as e:
        print(e)

# Captures images and rotates the turn table between each capture.    
def ProcessLineContent(turn, imageCount, camera):
    currentCount = 0    
    connection = serial.Serial('COM3', 115200)
    time.sleep(2)   # Wait for grbl to initialize
    connection.flushInput()  # Flush startup text in serial input

    while(currentCount < imageCount):
        CaptureImage(camera, currentCount + 1)  
        SendGCode(connection, turn)
        time.sleep(2)  
        currentCount += 1       
    connection.close()
    camera.StopLive()    
    cv2.destroyWindow('Window') 

if __name__ == "__main__":  
    # Creates the UI                     
    radio_choices = ['5', '10', '20', '30']    
    inputs = {}
    layout = [
    [sg.Text('Researcher:', justification='left', size=(10, 1)), sg.InputText(key='researcher')],
    [sg.Text('Location:', justification='left', size=(10, 1)), sg.InputText(key='location')
     ],
    [sg.Text('Foldername:', justification='left', size=(10, 1)), sg.InputText(key='folder')],
    [sg.Text('Filename:', justification='left', size=(10, 1)), sg.InputText(key='file')],
    [sg.Text('Description:', justification='left', size=(10, 1)), sg.InputText(key='description')],
    [sg.Text('Image Count:', justification='left', size=(10, 1)), sg.InputText(key='count')
     ],     
    [sg.Text('Rotation (in degrees):'), sg.Radio('5', "RADIO1", default=False, key=radio_choices[0]), sg.Radio('10', "RADIO1", default=False, key=radio_choices[1]), sg.Radio('20', "RADIO1", default=False, key=radio_choices[2]), sg.Radio('30', "RADIO1", default=False, key=radio_choices[3]), (sg.InputText(size=(10, 1), key='rotation'))],       
    [sg.Output(size=(60, 10))],
    [sg.Submit(), sg.Cancel()]
    ]
    turn = ""
    window = sg.Window('Single Seed Analysis', layout)
    while True:                             # The Event Loop
        event, values = window.read()
        #print('Image Count: {0}, Rotation: {1}'.format(values[0], values[1])) #debug
        if event in (None, 'Exit', 'Cancel'):
            break
            
            ## Code that defaults to a value of 10 degrees if no user input is provided.
            #if(not values[1]):
            #    print("No GCode for turn is provided. Defaulting to G21G91G1X0.088F51 which is 10 degrees.")    
            #    turn = 'G21G91G1X0.088F51'
            #    time.sleep(5)                
                
            #else:
                # turn degrees is converted to GCode units based on the assumption that 10 degrees is 0.088 in rotational units. A cross-multiplication is performed using the assumption
            #    turnDegrees = int(values[1])
            #    turn = 'G21G91G1X{}F51'.format((turnDegrees * 0.088)/10)
        try:
            #count = values['count']
            #print(count)
            if(values['count'] and int(values['count'])):            
                if(not values['researcher']):
                    values['researcher'] = "No name provided."
                    
                if(not values['location']):
                    values['location'] = "No location provided."

                if(not values['folder']):
                    values['folder'] = "Default"
                
                if(not values['file']):
                    values['file'] = "default"
                
                if(not values['description']):
                    values['description'] = "No description provided."
                                               
                if(values['rotation']):
                    turn = 'G21G91G1X{}F51'.format((int(values['rotation']) * 0.0889)/10)
                else:
                    for key in radio_choices:
                        if(values[key]):
                            turn = 'G21G91G1X{}F51'.format((int(key) * 0.0889)/10)
                            values['rotation'] = key
                    if(turn == ""):
                        turn = 'G21G91G1X{}F51'.format((10 * 0.0889)/10)
                        print('Rotation is not provided. Defaulting to 10 degrees.')
                        values['rotation'] = '10'
                                                
                
                # Finds the camera. 
                #camera = FindCamera()

                # Sets the parameters for the camera.
                #SetCamera(camera)
                
                CreateFolderandChangeDir(values['folder'])

                #ProcessLineContent(turn, int(values['count']), camera)   

                ReverttoParentDir()
                
                #volume = demo_carving.DemoCarve(values['folder'] + '/')

                # the main parameters we need to setup
                vintValue = 90  # the value of light
                pixPerMMAtZ = 76 / 3.945  # 95/3.945  # 145/5.74 # 94.5/3.945 #157/6.78 #94 /3.94
                imageWidth = 200
                imageHeight = 200

                # the source of the images
                path = 'C:\\Users\\marven\\Documents\\Spring-2021\\IC-Imaging-Control-Samples\\Python\\Open Camera, Grab Image to OpenCV\\pic\\Wheat-FlatTipEraserCrease\\'

                length, width, height, volume = CalculateVolume(path, vintValue, pixPerMMAtZ, imageWidth, imageHeight, False)
                
                CreateCSVFile(values['researcher'], values['location'], values['description'], values['count'], values['rotation'], values['file'], datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), length, width, height, volume)
        except Exception as e:            
            print(e)

