

#importing some useful packages
import matplotlib.pyplot as plt
import matplotlib.image as mpimg 
import numpy as np
import cv2
#########%matplotlib inline
import time
import imageio
                  
import moviepy

#from moviepy.audio.io.AudioFileClip 
##import AudioFileClip

import moviepy.Clip 

from moviepy.editor import VideoFileClip



###### define some globals for keeping track o slope

 
global AVERAGE_LEFT_SLOPE
global AVERAGE_RIGHT_SLOPE
global INIT_LEFT_SLOPE
global INIT_RIGHT_SLOPE
global NUM_SLOPE_CALC



global LEFT_UPPER_X_INTERCEPT 
global LEFT_UPPER_Y_INTERCEPT

global LEFT_LOWER_X_INTERCEPT
global LEFT_LOWER_Y_INTERCEPT

global RIGHT_UPPER_X_INTERCEPT
global RIGHT_UPPER_Y_INTERCEPT

global RIGHT_LOWER_X_INTERCEPT
global RIGHT_LOWER_Y_INTERCEPT




global LEFT_UPPER_X_INT_TOTAL 
global LEFT_LOWER_X_TOTAL
global RIGHT_UPPER_X_TOTAL
global RIGHT_LOWER_X_TOTAL


global NUM_LEFT_INTERCEPTS_SAVED
global NUM_RIGHT_INTERCEPTS_SAVED

                

#### INITIALIZE THEAVERAGE SLOPE TO ARBITRAY 45 DEGREE


LEFT_UPPER_X_INTERCEPT =500
LEFT_UPPER_Y_INTERCEPT =350

LEFT_LOWER_X_INTERCEPT =100
LEFT_LOWER_Y_INTERCEPT = 400 

RIGHT_UPPER_X_INTERCEPT =900
RIGHT_UPPER_Y_INTERCEPT=400

RIGHT_LOWER_X_INTERCEPT=900
RIGHT_LOWER_Y_INTERCEPT=400




AVERAGE_LEFT_SLOPE = .5

AVERAGE_RIGHT_SLOPE = -.5

INIT_LEFT_SLOPE=0
INIT_RIGHT_SLOPE =0

NUM_SLOPE_CALC=0   


NUM_LEFT_INTERCEPTS_SAVED = 0
NUM_RIGHT_INTERCEPTS_SAVED = 0

LEFT_UPPER_X_INT_TOTAL =0
LEFT_LOWER_X_INT_TOTAL =0
RIGHT_UPPER_X_INT_TOTAL =0 
RIGHT_LOWER_X_INT_TOTAL =0


 
######### define functions to be used
import math


def grayscale(img):
    """Applies the Grayscale transform
    This will return an image with only one color channel
    but NOTE: to see the returned image as grayscale
    (assuming your grayscaled image is called 'gray')
    you should call plt.imshow(gray, cmap='gray')"""
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Or use BGR2GRAY if you read an image with cv2.imread()
    # return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
def canny(img, low_threshold, high_threshold):
    """Applies the Canny transform"""
    return cv2.Canny(img, low_threshold, high_threshold)

def gaussian_blur(img, kernel_size):
    """Applies a Gaussian Noise kernel"""
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

def region_of_interest(img, vertices):
    """
    Applies an image mask.
    
    Only keeps the region of the image defined by the polygon
    formed from `vertices`. The rest of the image is set to black.
    """
    #defining a blank mask to start with
    mask = np.zeros_like(img)   
    
    #defining a 3 channel or 1 channel color to fill the mask with depending on the input image
    if len(img.shape) > 2:
        channel_count = img.shape[2]  # i.e. 3 or 4 depending on your image
        ignore_mask_color = (255,) * channel_count
    else:
        ignore_mask_color = 255
        
    #filling pixels inside the polygon defined by "vertices" with the fill color    
    cv2.fillPoly(mask, vertices, ignore_mask_color)
    
    #returning the image only where mask pixels are nonzero
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

def extendLinesDown(image, linex1, liney1 , slope):
    
    '''
    This function will calculate the x and y intercept points
    and use them to find the points needed to extend the lines.
          y = -x1*slope+y1
          y = mx + yintercept
          
          x = (maxy-yint)/slope
                  
     once you have the y intercept calculate the intercept with the x 
     axis and atmaxy
      '''
    slope=slope* -1.0
      
    yintercept = liney1 - float(slope * linex1)
      
    imshape = image.shape
    maxy = imshape[0]
          
    x_intercept = int((maxy-yintercept )/slope)
          
      
    return (  x_intercept,maxy )

#*************************************************************

def extendLinesUp(image, linex1, liney1 , slope):
    
    '''
    This function will calculate the x and y intercept points
        and use them to find the points needed to extend the lines.
  
          y = -x1*slope+y1
          y = mx + yintercept
          
          x = (maxy-yint)/slope
          
         
    once you have the y intercept calculate the intercept with the x 
    axis at y = 0( or at the horizon and at maxy
    '''
    slope=slope* -1.0
      
    yintercept = liney1 - float(slope * linex1)
  
     
    imshape = image.shape
    topWinInt = int(imshape[0]*0.64)   # top of window of interest  
      
    x_intercept = int((topWinInt-yintercept )/slope)

    return (  x_intercept, topWinInt )
    

def initializeInterceptGlobals(image):
    
    '''
    This function will initaialize the Intercepts Globals
    This is needed because the average slope and the 
    average intercept take a few frames to initialize
    
    '''
 
    global LEFT_UPPER_X_INTERCEPT 
    global LEFT_UPPER_Y_INTERCEPT
    
    global LEFT_LOWER_X_INTERCEPT
    global LEFT_LOWER_Y_INTERCEPT
    
    global RIGHT_UPPER_X_INTERCEPT
    global RIGHT_UPPER_Y_INTERCEPT
    
    global RIGHT_LOWER_X_INTERCEPT
    global RIGHT_LOWER_Y_INTERCEPT
    
    
    imshape = image.shape
    xMidpoint = int(imshape[1] / 2)
                             
    topWinInt = int(imshape[0]*0.64)   # This is where the lines go into the horizon  

    LEFT_UPPER_X_INTERCEPT =xMidpoint-50
    LEFT_UPPER_Y_INTERCEPT =topWinInt

    LEFT_LOWER_X_INTERCEPT =100
    LEFT_LOWER_Y_INTERCEPT = imshape[0]

    RIGHT_UPPER_X_INTERCEPT =xMidpoint+50
    RIGHT_UPPER_Y_INTERCEPT=topWinInt

    RIGHT_LOWER_X_INTERCEPT=imshape[1] - 100
    RIGHT_LOWER_Y_INTERCEPT= imshape[0]
    
    return




def draw_lines(img, lines, color=[255, 0, 0], thickness=4):
    """
    This is the function will try to filter through all the hough lines 
    to find the lines with the same slope as the lane lines.
    
    the slope will be averaged and stored as a global.
    
    All the lines that meet strict requirements will be averaged togather.
    these averaged lines will be combined to form one.
    
    This single line will be used along with the averaged slope to
    extend the line.
    
    
    The average line will BE EXTENDED UP TO A WORKING LINE EDGE AND 
    EXTENDED DOWN TO THE BOTTOM OF THE SCREEN.
    
    
    
    This function draws `lines` with `color` and `thickness`.    
    Lines are drawn on the image inplace (mutates the image).
    If you want to make the lines semi-transparent, think about combining
    this function with the weighted_img() function below
    
    GOING TO AVERAGE THE SLOPES FOR NOW
    """
 
    # Here are the  globals to hold essential data when out of the function
    global AVERAGE_LEFT_SLOPE
    global AVERAGE_RIGHT_SLOPE
    global INIT_LEFT_SLOPE
    global INIT_RIGHT_SLOPE
    global NUM_SLOPE_CALC
    
    global LEFT_LANE_AVERAGE

       
    global LEFT_UPPER_X_INTERCEPT 
    global LEFT_UPPER_Y_INTERCEPT

    global LEFT_LOWER_X_INTERCEPT
    global LEFT_LOWER_Y_INTERCEPT

    global RIGHT_UPPER_X_INTERCEPT
    global RIGHT_UPPER_Y_INTERCEPT

    global RIGHT_LOWER_X_INTERCEPT
    global RIGHT_LOWER_Y_INTERCEPT
    
    
    global LEFT_UPPER_X_INT_TOTAL 
    global LEFT_LOWER_X_INT_TOTAL
    global RIGHT_UPPER_X_INT_TOTAL
    global RIGHT_LOWER_X_INT_TOTAL


    global NUM_LEFT_INTERCEPTS_SAVED
    global NUM_RIGHT_INTERCEPTS_SAVED
   

               
    #Create arrays to keep track of left and right data
   
    

    
    minSlope= 0.3
    maxSlope= 0.8

    minNegSlope = -0.30
    minNegSlopeReset = -0.42
    maxNegSlope = -0.8  
    
    leftSlopeTotal = 0.0
     
    rightSlopeTotal = 0.0
    averageLeftSlopeThisFun=0
    minSlopesToAvg=7

 
    numLeft =0
    numRight =0                     
 
    numLines =0
    
    totalx1l =0
    totalx2l = 0
    totaly1l = 0
    totaly2l  =0
     
    totalx1r =0
    totalx2r = 0
    totaly1r = 0
    totaly2r  =0
      
    
    leftLinesSaved =0
    rightLinesSaved =0
    
    delta = 0.15
    
    rightDelta = 0.12
    
    minInterceptsBeforeUsing =5
    ratio1 = 0.8
    ratio2 = 0.2
    
    if NUM_SLOPE_CALC==0:
        initializeInterceptGlobals(img)# initialize the globals first time function is called
        
  
    for line in lines:
  
        numLines =0
               
                
        for x1,y1,x2,y2 in line:
            '''
            check the slope of line to get rid of horizontal lines
            
            if slope is greater than minSlope and slope < maxSlope30
            the line will be used for the left lane line.
            
            NOTE THE SLOPE IS INVERTED BECAUSE THE Y axis in the input
            and output images is reversed
            
            '''
            #slope =2
            slope = (float(y2)-y1)/(float(x2)-x1)
            #modify the sign of slope function to compensate for Y=0 at top
            slope = slope * -1.0
                
            midpoint = img.shape[1] / 2
                                
                                
            # temp test averageRightSlopeThisFun = -0.5
 
       
            if slope >= minSlope and slope < maxSlope: 
                '''
                This line will be considered for use in finding and
                creating the left lane 
                '''
                
                if NUM_SLOPE_CALC >= minSlopesToAvg:
                    #see if running average has been initialised 
                    if  slope >= (AVERAGE_LEFT_SLOPE - delta) and slope < (AVERAGE_LEFT_SLOPE + delta):

                        leftSlopeTotal = leftSlopeTotal + slope
                        numLeft +=1
                                             
                        if x1 < midpoint - 100 and x2 < midpoint+100:
                            '''
                            Try to get rid of as many guardrails and pavement borders
                            as possible
                            The current line has passed all slope tests.
                            time to average it
                            '''
                            
                            leftLinesSaved +=1
                            totalx1l  += x1
                            totalx2l  += x2
                            totaly1l  += y1
                            totaly2l  += y2
                        
                
            elif slope > maxNegSlope and slope < 0:#minNegSlope: 
                '''
                working on RIGHT lane slope
                '''
                
                if NUM_SLOPE_CALC >= minSlopesToAvg:
                    #use average3 slope to see if new line is valid
                    if slope >= (AVERAGE_RIGHT_SLOPE - rightDelta) and slope < (AVERAGE_RIGHT_SLOPE + rightDelta):

                        numRight= numRight+1
                
                        rightSlopeTotal = rightSlopeTotal + slope
 
                        
                        if  x1 > midpoint-100 and x2 > midpoint +50 and x2 <img.shape[1] - 50:                      
                           
                            rightLinesSaved = rightLinesSaved+1
                            totalx1r += x1
                            totalx2r += x2
                            totaly1r += y1
                            totaly2r += y2
                        
  

    numLines= numLines+1

    
   
    NUM_SLOPE_CALC += 1
    
    if AVERAGE_RIGHT_SLOPE > minNegSlope:
        print(" resetting right slope averae")
        AVERAGE_RIGHT_SLOPE = minNegSlopeReset
        
    if numLeft> 0:
        averageLeftSlopeThisFun = leftSlopeTotal/numLeft
    else:
        averageLeftSlopeThisFun=AVERAGE_LEFT_SLOPE
        
    if numRight >0:
        averageRightSlopeThisFun = rightSlopeTotal/numRight
        if averageRightSlopeThisFun >minNegSlope:
            averageRightSlopeThisFun=minNegSlopeReset
            print( " reset averageRightSlopeThisFun")
        
    else:
        averageRightSlopeThisFun=AVERAGE_RIGHT_SLOPE        

    #If we have an average slope going and there usable lines this function the update the slope    
    if averageLeftSlopeThisFun > 0 and  NUM_SLOPE_CALC >=minSlopesToAvg:
        AVERAGE_LEFT_SLOPE = (AVERAGE_LEFT_SLOPE*.9) + (averageLeftSlopeThisFun*.1) 
        
    #If we have an average slope going and there usable lines this function the update the slope    
    if averageRightSlopeThisFun < 0 and  NUM_SLOPE_CALC >=minSlopesToAvg:
        AVERAGE_RIGHT_SLOPE = (AVERAGE_RIGHT_SLOPE*.9) + (averageRightSlopeThisFun*.1)  

               
    
    # USE THE DATA IN THE   leftLinesSaved TO COMPUTE AND DRAW A SINGLE LINE
    if leftLinesSaved > 0:
        x1 = int( totalx1l/leftLinesSaved)
        x2 = int( totalx2l/leftLinesSaved)
        y1 = int( totaly1l/leftLinesSaved)
        y2 = int( totaly2l/leftLinesSaved)

        #EXTEND the lines down and up. GET NEW INTERCEPTS
        extDown_x, extDown_y=extendLinesDown(img, x1, y1, AVERAGE_LEFT_SLOPE )  #AVERAGE_LEFT_SLOPE)
        if extDown_x < 150:
            extDown_x = 150 

        extUp_x, extUp_y=extendLinesUp(img, x2, y2, AVERAGE_LEFT_SLOPE )  #AVERAGE_LEFT_SLOPE)
 

        ''' 
        See if average intercepts have been initialized
        '''
        if NUM_LEFT_INTERCEPTS_SAVED > minInterceptsBeforeUsing:
            
            '''
            Compute new intercept average using average intercept and the 
            new intercept data.
            '''
            LEFT_UPPER_X_INTERCEPT = int(LEFT_UPPER_X_INTERCEPT*ratio1 + extUp_x*ratio2 )
            LEFT_LOWER_X_INTERCEPT = int(LEFT_LOWER_X_INTERCEPT*ratio1 + extDown_x*ratio2)

            LEFT_UPPER_Y_INTERCEPT = extUp_y
            LEFT_LOWER_Y_INTERCEPT = extDown_y   
            
            cv2.line(img, (LEFT_LOWER_X_INTERCEPT, extDown_y), (LEFT_UPPER_X_INTERCEPT, extUp_y), color, 3)
            
            
           
            
        elif NUM_LEFT_INTERCEPTS_SAVED < minInterceptsBeforeUsing:  #just use the current intercept  

            #continue to initialize the average intercepts
            LEFT_UPPER_X_INT_TOTAL += extUp_x
            LEFT_LOWER_X_INT_TOTAL += extDown_x
            
            

            
            cv2.line(img, (extDown_x, extDown_y), (extUp_x, extUp_y), color, 3)

            
        elif NUM_LEFT_INTERCEPTS_SAVED == minInterceptsBeforeUsing:
            LEFT_UPPER_X_INTERCEPT = int(LEFT_UPPER_X_INT_TOTAL/minInterceptsBeforeUsing)
            LEFT_LOWER_X_INTERCEPT = int(LEFT_LOWER_X_INT_TOTAL/minInterceptsBeforeUsing)
            print(" JUST INTIALIZED THE LEFT INTERCEPT")
             
            cv2.line(img, (extDown_x, extDown_y), (extUp_x, extUp_y), color, 3)
            
        NUM_LEFT_INTERCEPTS_SAVED +=1

    else: # no new good lines use saved lines
    
  
        cv2.line(img, (LEFT_LOWER_X_INTERCEPT, LEFT_LOWER_Y_INTERCEPT), (LEFT_UPPER_X_INTERCEPT, LEFT_UPPER_Y_INTERCEPT), color, 3)
    
    
    
    # USE THE DATA IN THE rightLinesSaved TO COMPUTE AND DRAW A SINGLE LINE

    if rightLinesSaved > 0:
        x1 = int( totalx1r/rightLinesSaved)
        x2 = int( totalx2r/rightLinesSaved)
        y1 = int( totaly1r/rightLinesSaved)
        y2 = int( totaly2r/rightLinesSaved)

 
        extDown_x, extDown_y=extendLinesDown(img, x2, y2, AVERAGE_RIGHT_SLOPE )  #AVERAGE_RIGHT_SLOPE)
       
        img.shape[1]
        
        if extDown_x > img.shape[1]:
            extDown_x = img.shape[1]-100 
                                 
                                 
                                 
        midpoint = int(img.shape[1] / 2)
     
                                 
        extUp_x, extUp_y=extendLinesUp(img, x1, y1, AVERAGE_RIGHT_SLOPE ) 
        
        
        if extUp_x < midpoint:
            extUp_x = midpoint
 
        
        ''' 
        See if average intercepts have been initialized
        '''
 
        if NUM_RIGHT_INTERCEPTS_SAVED > minInterceptsBeforeUsing:
            
            '''
            Compute new intercept average using average intercept and the 
            new intercept data.
            '''
            RIGHT_UPPER_X_INTERCEPT = int(RIGHT_UPPER_X_INTERCEPT*ratio1 + extUp_x*ratio2 )
            RIGHT_LOWER_X_INTERCEPT = int(RIGHT_LOWER_X_INTERCEPT*ratio1 + extDown_x*ratio2)

            RIGHT_UPPER_Y_INTERCEPT = extUp_y
            RIGHT_LOWER_Y_INTERCEPT = extDown_y   
            
            cv2.line(img, (RIGHT_LOWER_X_INTERCEPT, extDown_y), (RIGHT_UPPER_X_INTERCEPT, extUp_y), color, 3)
           
            
        elif NUM_RIGHT_INTERCEPTS_SAVED < minInterceptsBeforeUsing:  #just use the current intercept  

            #continue to initialize the average intercepts
            RIGHT_UPPER_X_INT_TOTAL += extUp_x
            RIGHT_LOWER_X_INT_TOTAL += extDown_x
            
            cv2.line(img, (extDown_x, extDown_y), (extUp_x, extUp_y), color, 3)

            
        elif NUM_RIGHT_INTERCEPTS_SAVED == minInterceptsBeforeUsing:
            RIGHT_UPPER_X_INTERCEPT = int(RIGHT_UPPER_X_INT_TOTAL/minInterceptsBeforeUsing)
            RIGHT_LOWER_X_INTERCEPT = int(RIGHT_LOWER_X_INT_TOTAL/minInterceptsBeforeUsing)
            print(" JUST INTIALIZED THE RIGHT INTERCEPT")
             
            cv2.line(img, (extDown_x, extDown_y), (extUp_x, extUp_y), color, 3)
            
        NUM_RIGHT_INTERCEPTS_SAVED +=1

    else: # no new good lines use saved lines
    
 
        cv2.line(img, (RIGHT_UPPER_X_INTERCEPT , RIGHT_UPPER_Y_INTERCEPT), ( RIGHT_LOWER_X_INTERCEPT,  RIGHT_LOWER_Y_INTERCEPT), color, 3)
    


    '''
    initializing slope average
    When starting out the average needs to be set up before using
    '''
                
    if NUM_SLOPE_CALC < minSlopesToAvg:
        if averageRightSlopeThisFun > minNegSlope:
            averageRightSlopeThisFun= minNegSlopeReset
            print(" reseting right slope AVERAGE_RIGHT_SLOPE",AVERAGE_RIGHT_SLOPE )
            INIT_LEFT_SLOPE= INIT_LEFT_SLOPE+ averageLeftSlopeThisFun
            INIT_RIGHT_SLOPE= INIT_RIGHT_SLOPE+ averageRightSlopeThisFun
       
       
    elif AVERAGE_LEFT_SLOPE==minSlopesToAvg:
       AVERAGE_LEFT_SLOPE = INIT_LEFT_SLOPE/minSlopesToAvg
       AVERAGE_RIGHT_SLOPE = INIT_RIGHT_SLOPE/minSlopesToAvg
             
       
       

def hough_lines(img, rho, theta, threshold, min_line_len, max_line_gap):
    """
    `img` should be the output of a Canny transform.
        
    Returns an image with hough lines drawn.
    """
    lines = cv2.HoughLinesP(img, rho, theta, threshold, np.array([]), minLineLength=min_line_len, maxLineGap=max_line_gap)
    line_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
    draw_lines(line_img, lines)
    return line_img

# Python 3 has support for cool math symbols.

def weighted_img(img, initial_img, α=0.8, β=1., λ=0.):
    """
    `img` is the output of the hough_lines(), An image with lines drawn on it.
    Should be a blank image (all black) with lines drawn on it.
    
    `initial_img` should be the image before any processing.
    
    The result image is computed as follows:
    
    initial_img * α + img * β + λ
    NOTE: initial_img and img must be the same shape!
    """
    return cv2.addWeighted(initial_img, α, img, β, λ)



def process_image(image):
    
    '''
     THIS PIPELINE WILL BE RUN ON EVERY IMAGE IN THE INPUT FILE
     
     The first few functions were provided as a framework.
     Theses will generate the lines from the image.
     
     we are only concerned with the lines in the bottom defined by
       image = region_of_interest(image, vertices)
       
       I use vertices to create the mask to get rid of most of the unwanted lines
     
     
    '''
    
    
 
    # Make a copy of image to be used at the end of the function
    initial_img = image
    
    #Convert to Grayscale to make image easeier to process
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) #grayscale conversion
    #plt.imshow(image, cmap='gray')

    #Use the CAnny function to find the edges
    image = canny(image, 50, 150)     #50,100

    plt.imshow(image)  # snapshot


    image = gaussian_blur(image, 5)

    plt.imshow(image)  # snapshot
   
    # This time we are defining a four sided polygon to mask
    imshape = image.shape
    '''
    This was the starting pointvertices = np.array([[(0,imshape[0]),(30, 300), (50, 300), (imshape[1],imshape[0])]], dtype=np.int32)

    NOTE THIS WAS HARDWIRED FOR IMAGES OF A FIXED SIZE.
    
    I use the following variables to customize the window size for the 
    actural image we read.
    
    
    '''
    midpoint = int(imshape[1] / 2.0 )
    max_x = imshape[1] - 100
    
    midpointLeft = midpoint-100
    midpointRight  = midpoint + 100 

    topWinInt = int(imshape[0]*0.64)   # top of window of interest  

               
 
    '''
    Watch out for stinking None type error when assigning vertices 
     Wasted 1.4 hours on this issue.
    '''
            
    # quite recent vertices = np.array([[(100,imshape[0]) ,(midpointLeft, 350), (midpointRight, 350), (850,imshape[0])]]    ,dtype=np.int32    )
    vertices = np.array([[(100,imshape[0]) ,(midpointLeft,topWinInt ), (midpointRight, topWinInt), (max_x,imshape[0])]]    ,dtype=np.int32    )

 
    image = region_of_interest(image, vertices)
    line_image = np.copy(image)*0 # creating a blank to draw lines on
  

    '''
    # The next function will generagte hough_lines then call my function
    draw_lines to draw the lane lines.
    
    draw_lines has the majority of the custom code in this file.
    
    '''
    
    image = hough_lines(image, rho, theta, threshold, min_line_len, max_line_gap)
 
    plt.imshow(image)  # snapshot this is it for now

    image = weighted_img(image, initial_img, α=0.8, β=1., λ=0.)

    return image



 
     
rho = 1 # distance resolution in pixels of the Hough grid
theta = np.pi/180 # angular resolution in radians of the Hough grid
threshold = 30   # was 36 minimum number of votes (intersections in Hough grid cell)
min_line_len = 50 #45minimum number of pixels making up a line
max_line_gap = 110   # 70maximum gap in pixels between connectable line segments

 ####==========================================================
 #####===========================================================
 
  


#######Create the output MPEG file
challenge_output = 'BestSolidYellowLeft.mp4' 

#read in the MPEG file
#clip2 = VideoFileClip('solidWhiteRight.mp4') 
clip2 = VideoFileClip('solidYellowLeft.mp4') 
#clip2 = VideoFileClip('challenge.mp4') 
#clip2 = VideoFileClip('test_images/solidYellowLeft.jpg') 

#test_images/solidYellowLeft.jpg

#Perform all the processing on the image

challenge_clip = clip2.fl_image(process_image) 

#Save the output to the ouput file you crated above.
challenge_clip.write_videofile(challenge_output, audio=False) 

