import cv2 as cv
import numpy as np
import mss

class Classbot:
    def __init__(self,main_img,temp_img=""):
        self.tempimg = temp_img
        self.mainimg = main_img
        if temp_img != "":
            self.tempimg = cv.imread(temp_img,cv.IMREAD_ANYCOLOR)
        
    def search(self,threshold=0.9,debug=False,mytxt=""):   
        result = cv.matchTemplate(self.mainimg,self.tempimg,cv.TM_CCOEFF_NORMED)    
        _,maxval,_,maxloc = cv.minMaxLoc(result)
        locations = np.where(result >= threshold)
        locations= list(zip(*locations[::-1]))
        #print(locations)
        height = self.tempimg.shape[0]
        width =  self.tempimg.shape[1]
        #print(maxval) ## ค่าความแม่นยำ
        #print(maxloc) ##  xy ที่เจอ จะเจอมุมซ้ายบนเสมอ
        rectangles =[]
        for loc in locations:
            rect = [int(loc[0]),int(loc[1]),width,height]
            rectangles.append(rect)
            rectangles.append(rect)
        point = []
        rectangles,_ =cv.groupRectangles(rectangles,groupThreshold=1,eps=0.2)
        #print(len(rectangles))
        if len(rectangles):
            for (x,y,w,h) in rectangles:
                topleft = (x,y)
                bottomright = (x+w,y+h)
                #get x y 
                centerx = x + int( w / 2)
                centery = y +int( h / 2)
                ##add x y to point for click
                point.append((centerx,centery))
                if debug:
                    #puttxt
                    font = cv.FONT_ITALIC
                    #position
                    position = (topleft[0],topleft[1]-10)
                    #fontsize
                    fontsize = 0.5
                    #color
                    color = (255,0,255)
                    cv.putText(self.mainimg,mytxt,position,font,fontsize,color,thickness=2)
                    cv.rectangle(self.mainimg,topleft,bottomright,color=(255,0,255),thickness=2,lineType=cv.LINE_8)
                    cv.drawMarker(self.mainimg,(centerx,centery),color=(255,255,0),thickness=2,markerSize=40,markerType=cv.MARKER_CROSS)
        else:
            pass
            #print("ไม่เจอรูปภาพ")
        if debug:
            print(f"เจอรูปภาพทั้งหมด = {len(rectangles)}")
            print(point)
            ##show
            cv.imshow("result",self.mainimg) 
        return point
    
    def searchArea(self,threshold=0.9,debug=False,rectangle=(0,0,0,0)):   
        result = cv.matchTemplate(self.mainimg,self.tempimg,cv.TM_CCOEFF_NORMED)    
        _,maxval,_,maxloc = cv.minMaxLoc(result)
        locations = np.where(result >= threshold)
        locations= list(zip(*locations[::-1]))
        #print(locations)
        height = self.tempimg.shape[0]
        width =  self.tempimg.shape[1]
        #print(maxval) ## ค่าความแม่นยำ
        #print(maxloc) ##  xy ที่เจอ จะเจอมุมซ้ายบนเสมอ
        rectangles =[]
        for loc in locations:
            rect = [int(loc[0]),int(loc[1]),width,height]
            rectangles.append(rect)
            rectangles.append(rect)
        point = []
        rectangles,_ =cv.groupRectangles(rectangles,groupThreshold=1,eps=0.2)
        #print(len(rectangles))
        if len(rectangles):
            for (x,y,w,h) in rectangles:
                #get x y 
                centerx = x + int( w / 2)
                centery = y +int( h / 2)
                ##add x y to point for click
                point.append((centerx,centery))
        else:
            pass
            #print("ไม่เจอรูปภาพ")
        if debug:
            x, y, width, height = rectangle
            ##show when not detect
            cv.rectangle(self.mainimg,(x,y),(width,height),color=(255,0,255),thickness=3,lineType=cv.LINE_8)
            cv.imshow("result",self.mainimg)  
               
        if len(point):
            checkpoint = self.is_inside_rectangle(rectangle,point,debug=debug)
        else:
            checkpoint= False
            point =(-1,-1)     
        return checkpoint,point
    
    def is_inside_rectangle(self,rectangle, point,debug=False):
        status = False
        x, y, width, height = rectangle
        if len(point):
            x_point = point[0][0]
            y_point =point[0][1]
        else:
            x_point =-1
            y_point =-1 
              
              
        if x <= x_point <= x + width and y <= y_point <= y + height:
            if debug:   
                cv.rectangle(self.mainimg,(x,y),(width,height),color=(0, 255, 0),thickness=3,lineType=cv.LINE_8)
                cv.drawMarker(self.mainimg,(x_point,y_point),color=(0, 255, 0),thickness=3,markerSize=40,markerType=cv.MARKER_CROSS)
                cv.imshow("result",self.mainimg) 
            status = True
        else:
            if debug: 
                cv.rectangle(self.mainimg,(x,y),(width,height),color=(255,0,255),thickness=3,lineType=cv.LINE_8)
                cv.drawMarker(self.mainimg,(x_point,y_point),color=(255,0,255),thickness=3,markerSize=40,markerType=cv.MARKER_CROSS)
                cv.imshow("result",self.mainimg) 
            status = False
        return status

        
    def getcolor(self,x,y,color="0x000000"):
        ##define status
        status = False 
        ## return b g r from x y[y,x]
        b,g,r = self.mainimg[y,x]
        #sumvalue from r g b
        sumvalue = self.mainimg[y,x].sum()
     
        ## change to r g b
        value = '%02x%02x%02x' % (r, g, b)
        ## upper 
        value =value.upper()
        ## add 0x autoitinfo
        value = '0x' + value
        ### if to return
        if value == color:
            status = True
        return status,sumvalue
    
    
    
    
    
    
    