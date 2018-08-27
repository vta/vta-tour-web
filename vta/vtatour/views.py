import os
import sys
import time
import math
import json
import hmac
import base64
import urllib2
import hashlib
import pymysql.cursors
#import pymysql
import urlparse
import datetime
import commands
import requests
import threading
import subprocess
import numpy as np
import mysql.connector
import google_streetview.api
from firebase import firebase
from django.conf import settings
import xml.etree.ElementTree as ET
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from math import cos, sin, atan2, sqrt, radians, degrees, asin, modf

global fps,firebase,google_key,api_key


fps='2' # Set video frame rate (frames per second)

api_url =  getattr(settings, "API_URL", None)
google_key = getattr(settings, "G_KEY", None)

def createdir(path):
    try:
        os.makedirs(path)
    except:
        pass

def mysql_post(query):
    try:
        my_host = getattr(settings, "DB_HOST", None)
        my_user = getattr(settings, "DB_USER", None)
        my_password = getattr(settings, "DB_PASSWORD", None)
        my_db = getattr(settings, "DB_DB", None)
	mydb = pymysql.connect(user=my_user,passwd=my_password,host=my_host,database=my_db)
        mycursor = mydb.cursor()
        mycursor.execute(query)
        mydb.commit()
        mycursor.close()
        mydb.close()
    except:
        pass
def mysql_get(query):
    try:
        my_host = getattr(settings, "DB_HOST", None)
        my_user = getattr(settings, "DB_USER", None)
        my_password = getattr(settings, "DB_PASSWORD", None)
        my_db = getattr(settings, "DB_DB", None)
	mydb = pymysql.connect(user=my_user,passwd=my_password,host=my_host,database=my_db)
        mycursor = mydb.cursor()
        mycursor.execute(query)
        stats = mycursor.fetchall()
        mycursor.close()
        mydb.close()
        for i in range(len(stats)):
            try:
                if stats[i].isalpha():
                    stats[i] = unicode(stats[i], "utf-8")
            except:
                pass
        
        return stats
    except Exception as x:
        print x
        pass
class Google(object):
    

    def download(self,data):

        if 1==1: # checks if data has 4 elements
            if data[0]=='rid': #checks if the first element is 'rid'
                m=0 #Sets file number to 0
                routename = data[1] # Stores route id into routename
                dirid = data[2] # Stores direction into dirid
                camangle = data[3] # Stores view into camangle
                ores=data[4] # original resolution
                env = data[5]
                dirname = routename +'/'+ dirid+'_'+ores+'_'+env #Stores base path of video directories
                video = routename+"_"+dirid+'_'+ores+'_'+env #Base name of the video
                sqldir=dirid
                if ores=="High":
                    resln=1280 
                if ores=="Low":
                    resln=640 


                sql = 'SELECT EXISTS(SELECT * FROM routes_progress WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'");'
                stats=mysql_get(sql)
                
                if(stats[0][0]==0):
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql1 = 'INSERT INTO routes_progress (route_id,direction,view,min,resolution,environment) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+currentmin+'","'+ores+'","'+env+'")'
                    mysql_post(sql1)

                sql2 = 'UPDATE routes_progress SET gen_status=0 WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                sql2 = 'UPDATE routes_progress SET gen_status=0,min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mysql_post(sql2)

                #Prints route id and direction in terminal
                 
                base_dir = '/var/www/html/vta' #Base directory
                
                pdir='/' # Project directory
                sdata=list();
                fkmlcords=list();
                lkmlcords=list();
                rkmlcords=list();
                bkmlcords=list();
                
                fwdkml=list();
                lftkml=list();
                rgtkml=list();
                bckkml=list();
                del fwdkml[:]               
                del lftkml[:]               
                del rgtkml[:]
                del bckkml[:]

                fkml=list();
                del fkml[:]
                del fkmlcords[:]
                del rkmlcords[:]
                del lkmlcords[:]
                del bkmlcords[:]
                del sdata[:]
                m1=0
                m2=0
                m3=0
                m4=0
                eletmp=0.0
                total=11000
                avg=0
                npy=0
                
                '''
                Status is set to zero if coordinates are fetched from firebase
                Status is set to one if coordinates are fetched from kml
                '''
                try:
                    os.system('rm -r -f '+base_dir+'/'+dirname+'/')
                except:
                    pass
                
                sdata = self.firedata(routename,dirid,base_dir,pdir,sqldir,camangle,env) # Gets coordinates from firebase
                # If no coordinates are present in firebase ,execution will stop here                
                if sdata==0:
                    try:
                        #If View is Left, Right or Backward Overwrites 405 to progress file (UI will display create forward first)
                        
                        currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                        sql5 = 'UPDATE routes_progress SET progress="No coordinates found in database." , min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                        mysql_post(sql5)

                    except Exception as x:
                        sql6 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                        mysql_post(sql6)

                    return 0
                
                # Creates video directories
                try:
                    createdir(base_dir+pdir+dirname+'/original')
                    createdir(base_dir+pdir+dirname+'/original/left')
                    createdir(base_dir+pdir+dirname+'/original/right')
                    createdir(base_dir+pdir+dirname+'/original/forward')
                    createdir(base_dir+pdir+dirname+'/original/backward')
                    createdir(base_dir+pdir+dirname+'/cropped')
                    createdir(base_dir+pdir+dirname+'/cropped/left')
                    createdir(base_dir+pdir+dirname+'/cropped/right')
                    createdir(base_dir+pdir+dirname+'/cropped/forward')
                    createdir(base_dir+pdir+dirname+'/cropped/backward')
                except:
                    pass
                tang= 0
                vtemp=0

                for i in range(0,len(sdata)):
                    import json

                    '''
                    oldpano : Panorama id of the current coordinate
                    newpano : Panorama id of the adjacent coordinate

                    newpano and oldpano are used to compare adjacent coordinates 
                    with their pano id to avoid downloading duplicate images.

                    Each street view image has a unique Panorama id
                    
                    If Panorama ids are same the the images will be same too
                    
                    If value of oldpano is same as newpano then download will skip 
                    and next two coordinates are compared  

                    '''

                    if(i==0): 
                        newpano = 'init_0' # Define newpano ,value doesn't matter
                        oldpano = newpano # Define oldpano
                        ocord = sdata[0] # ocord is used to store the current coordinate 
                    
                    if i<len(sdata)-1:
                        rcord=sdata[i+1].replace(" ","") # rcord is used to store the adjacent coordinate

                    try:
                        # Compares adjacent coordinates to avoid downloading duplicate images
                        # Stores the metadata response(JSON) of rcord into htmltext
                        result = urllib2.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?location='+rcord+'&key='+google_key)
                        htmletxt = result.read()
                        # Converts it into JSON format and stores it into snap
                        snap = json.loads(htmletxt)
                        if snap['status'] == 'ZERO_RESULTS':
                            continue   
                    
                        # Panorama id of rcord is stored into newpano
                        newpano = snap['pano_id'] 

                        '''
                        Checks if both panorama ids are same,if not set rm=1 
                        If rm=1 image is downloaded with the coordinates present in ocord

                        '''
                        if (oldpano!=newpano):  
                            print oldpano , newpano
                            oldpano=newpano
                            rm=1
                        else:
                            rm=0
                    except:
                        # rm=0
                        pass
                    

                    if(rm==1): # If rm is 1 download the images
                        try:    
                            try:
                                   # Splits ocord into latitude and longitude
                                a = ocord.split(',') 
                                # Splits rcord into latitude and longitude 
                                b = rcord.split(',') 
                                
                                a1 = float(a[0]) #lat of ocord
                                a2 = float(a[1]) #lng of ocord
                                b1 = float(b[0]) #lat of rcord
                                b2 = float(b[1]) #lng of rcord

                            except Exception as x:
                                sql8 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                                mysql_post(sql8)
                                pass 
                            ang=int(self.calculate_initial_compass_bearing((a1,a2),(b1,b2))) # Calculate the Heading angle (Bearing angle)
                            
                            prog=(float(i)/(len(sdata)))*100 # Calculate the progress
                            
                            '''
                            Creates threads to download each Street view image
                            All threads are set to daemon (daemon thread closes automatically)
                            
                            Images are downloaded using grabimage() 

                            grabimage(coordinates,angle,resolution,basedirectory,projectdirectory,videodirectory,view,filenumber)
                                   
                            '''
                            currentmin = str(os.popen('date +"%M"').read()).replace("\n","")

                            sql9 = 'UPDATE routes_progress SET progress="Downloading images : '+str(int(prog))+'% Completed",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                            mysql_post(sql9)
                            if (camangle=='Forward') or (camangle=='All'):
                                fwd=threading.Thread(target=self.grabimage,args=(ocord,ang+0,resln,base_dir,pdir,dirname,'forward',m1,))
                                fwd.setDaemon(True)
                                fwd.start()
                            if (camangle=='Backward') or (camangle=='All'):
                                bck=threading.Thread(target=self.grabimage,args=(ocord,ang+180,resln,base_dir,pdir,dirname,'backward',m2,))
                                bck.setDaemon(True)
                                bck.start()
                                
                            if (camangle=='Left') or (camangle=='All'):
                                lft=threading.Thread(target=self.grabimage,args=(ocord,ang+270,resln,base_dir,pdir,dirname,'left',m3,))
                                lft.setDaemon(True)
                                lft.start()
                               
                            if (camangle=='Right') or (camangle=='All'):
                                rgt=threading.Thread(target=self.grabimage,args=(ocord,ang+90,resln,base_dir,pdir,dirname,'right',m4,))
                                rgt.setDaemon(True)
                                rgt.start()
                               
                            
                            try:

                                if (camangle=='Forward') or (camangle=='All'):
                                        try:
                                            fwd.join()
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/forward/"+str(m1)+".jpg").st_size)/1000)>10):
                                                if(i!=0):
                                                    try:
                                                        d = commands.getstatusoutput('compare -metric FUZZ '+base_dir+pdir+dirname+'/original/forward/'+str(m1)+'.jpg '+base_dir+pdir+dirname+'/original/forward/'+str(m1-1)+'.jpg NULL:')
                                                        val2 = d[1].split(" ")
                                                    except:
                                                        pass
                                                    if(val2[0]=='compare:'):
                                                        val2[0]=1
                                                    if (float(val2[0])!=0):
                                                        m1=m1+1
                                                        fkmlcords.append(ocord) #ocord is added to kml array for kml creation
                                        except Exception as x:
                                            pass
                                   

                                if (camangle=='Right') or (camangle=='All'):
                                        try:
                                            rgt.join()
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/right/"+str(m4)+".jpg").st_size)/1000)>10):
                                                if(i!=0):
                                                    try:
                                                        d = commands.getstatusoutput('compare -metric FUZZ '+base_dir+pdir+dirname+'/original/forward/'+str(m4)+'.jpg '+base_dir+pdir+dirname+'/original/forward/'+str(m4-1)+'.jpg NULL:')
                                                        val2 = d[1].split(" ")
                                                    except:
                                                        pass
                                                    if(val2[0]=='compare:'):
                                                        val2[0]=1
                                                    if (float(val2[0])!=0):
                                                        m4=m4+1
                                                        rkmlcords.append(ocord)
                                        except Exception as x:
                                            pass
                                if (camangle=='Backward') or (camangle=='All'):
                                        try:
                                            bck.join()
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/backward/"+str(m2)+".jpg").st_size)/1000)>10):
                                                if(i!=0):
                                                    try:
                                                        d = commands.getstatusoutput('compare -metric FUZZ '+base_dir+pdir+dirname+'/original/forward/'+str(m2)+'.jpg '+base_dir+pdir+dirname+'/original/forward/'+str(m2-1)+'.jpg NULL:')
                                                        val2 = d[1].split(" ")
                                                    except:
                                                        pass
                                                    if(val2[0]=='compare:'):
                                                        val2[0]=1
                                                    if (float(val2[0])!=0):
                                                        m2=m2+1
                                                        bkmlcords.append(ocord)
                                        except:
                                            pass
                                if (camangle=='Left') or (camangle=='All'):
                                        try:
                                            lft.join()
                                            if ((float(os.stat(base_dir+pdir+dirname+"/original/left/"+str(m3)+".jpg").st_size)/1000)>10):
                                                if(i!=0):
                                                    try:
                                                        d = commands.getstatusoutput('compare -metric FUZZ '+base_dir+pdir+dirname+'/original/forward/'+str(m3)+'.jpg '+base_dir+pdir+dirname+'/original/forward/'+str(m3-1)+'.jpg NULL:')
                                                        val2 = d[1].split(" ")
                                                    except:
                                                        pass
                                                    if(val2[0]=='compare:'):
                                                        val2[0]=1
                                                    if (float(val2[0])!=0):
                                                        m3=m3+1 # Increment file number
                                                        lkmlcords.append(ocord)
                                        except Exception as x:
                                            pass                                    
                                ocord=rcord                  
                            except Exception as x:
                                
                                ocord = rcord # To download next image
                                sql10 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                                mysql_post(sql10)
                                pass
                            
                        except Exception as x:
                            sql11 = 'INSERT INTO error_log (route_id,direction,view,resolution,environment,log) VALUES ('+routename+',"'+sqldir+'","'+camangle+'","'+ores+'","'+env+'","'+str(x)+'")'
                            mysql_post(sql11)
                            pass
                
                if (camangle=='Forward') or (camangle=='All'):
                    fwdkml=self.cropfunc(base_dir,pdir,dirname,'Forward',resln,fkmlcords)
                if (camangle=='Backward') or (camangle=='All'):
                    bckkml=self.cropfunc(base_dir,pdir,dirname,'Backward',resln,bkmlcords)
                if (camangle=='Left') or (camangle=='All'):
                    lftkml=self.cropfunc(base_dir,pdir,dirname,'Left',resln,lkmlcords)
                if (camangle=='Right') or (camangle=='All'):
                    rgtkml=self.cropfunc(base_dir,pdir,dirname,'Right',resln,rkmlcords)

                
                #retrive aws credentials from django
                aws_key = getattr(settings, "AWS_"+env.upper()+"_KEY", None)
                aws_secret = getattr(settings, "AWS_"+env.upper()+"_SECRET", None)
                current_date = str(os.popen('date').read()).replace(" ","_").replace("\n","")
                if (camangle=='Forward') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql12 = 'UPDATE routes_progress SET progress="99% Completed ( Generating forward video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql12)

                    #Creates forward video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/forward/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.mp4')
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql13 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading forward video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql13)
                    #Uploads forward video to s3
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                                       
                
                if (camangle=='Backward') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql14 = 'UPDATE routes_progress SET progress="99% Completed ( Generating backward video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql14)
                    #Creates backward video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/backward/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.mp4')
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql15 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading backward video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql15)
                    #Upload backward video to s3
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                    
                
                if (camangle=='Left') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql16 = 'UPDATE routes_progress SET progress="99% Completed ( Generating left video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql16)
                    #Create Left video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/left/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.mp4')
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql17 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading left video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql17)
                    #Upload left video to s3
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                    

                if (camangle=='Right') or (camangle=='All'):
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql18 = 'UPDATE routes_progress SET progress="99% Completed ( Generating right video ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql18)
                    #Create right video using FFMPEG
                    os.system('/usr/bin/ffmpeg -framerate '+fps+' -y -i '+base_dir+pdir+dirname+'/cropped/right/'+'%d_cropped.jpg -c:v libx264 -preset slow -crf 22 -loglevel quiet '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.mp4')
                    #Upload right video to s3
                    
                    currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                    sql19 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading right video to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                    mysql_post(sql9)
                    os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.mp4 '+api_url+env+'/'+routename+'/ --acl public-read-write')
                    
                
                fb_url=getattr(settings, "FB_"+env.upper()+"", None)

                
                url = fb_url+routename+"/"+dirid+""

                url_forward=routename+'/'+current_date+'_'+video+'_forward.mp4'
                url_backward=routename+'/'+current_date+'_'+video+'_backward.mp4'
                url_right=routename+'/'+current_date+'_'+video+'_right.mp4'
                url_left=routename+'/'+current_date+'_'+video+'_left.mp4'
                url_kml=routename+'/'+current_date+'_'+video+'.kml'
                url_fkml=routename+'/'+current_date+'_'+video+'_forward.kml'
                url_lkml=routename+'/'+current_date+'_'+video+'_left.kml'
                url_rkml=routename+'/'+current_date+'_'+video+'_right.kml'
                url_bkml=routename+'/'+current_date+'_'+video+'_backward.kml'

                api_key=getattr(settings,"API_KEY",None)
                api_token=getattr(settings,"API_TOKEN",None)

                
                if (camangle=='Forward') or (camangle=='All'):
                    payload = '{\n  \"videoUrl\":\"'+url_forward+'\",\n  \"KmlUrl\":\"'+url_fkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/front", data=payload, headers=headers)
                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Forward_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mysql_post(sql20)

                    sql21 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Forward","'+url_forward+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql21)

                    sql25 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Forward","'+url_fkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql25)

                if (camangle=='Backward') or (camangle=='All'):
                    payload = '{\n  \"videoBackUrl\":\"'+url_backward+'\",\n  \"KmlUrlBack\":\"'+url_bkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/back", data=payload, headers=headers)

                 
                                    
                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Backward_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mysql_post(sql20)

                    sql22 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Backward","'+url_backward+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql22)
                    
                    sql25 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Backward","'+url_bkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql25)
                
                if (camangle=='Left') or (camangle=='All'):
                    payload = '{\n  \"videoLeftUrl\":\"'+url_left+'\",\n  \"KmlUrlLeft\":\"'+url_lkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/left", data=payload, headers=headers)

                   
                    
                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Left_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mysql_post(sql20)

                    sql23 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Left","'+url_left+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql23)
                    
                    sql25 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Left","'+url_lkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql25)


                if (camangle=='Right') or (camangle=='All'):
                    payload = '{\n  \"videoRightUrl\":\"'+url_right+'\",\n  \"KmlUrlRight\":\"'+url_rkml+'\"\n}'

                    headers = {
                        'content-type': "application/json",
                        'apikey': api_key,
                        'cache-control': "no-cache"                        
                        }

                    response = requests.request("POST",fb_url+str(ores.lower())+"-resolution/"+str(routename)+"/"+str(dirid)+"/right", data=payload, headers=headers)

                    sql20 = "INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ("+routename+",'"+sqldir+"','Right_API_Response','"+str(response.text)+"','"+current_date+"','"+ores+"','"+env+"')"
                    mysql_post(sql20)

                    sql24 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","VIDEO_Right","'+url_right+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql24)

                    sql25 = 'INSERT INTO routes_log (route_id,direction,type,url,date_time,resolution,environment) VALUES ('+routename+',"'+sqldir+'","KML_Right","'+url_rkml+'","'+current_date+'","'+ores+'","'+env+'")'
                    mysql_post(sql25)

       
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                sql26 = 'UPDATE routes_progress SET progress="99% Completed ( Done uploading videos ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mysql_post(sql26)

                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                sql27 = 'UPDATE routes_progress SET progress="99% Completed ( Generating KML ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mysql_post(sql27)
                
                if (camangle=='Forward') or (camangle=='All'):
                    try:
                        dutn=0
                        #stores the duration of forward video to dutn 
                        dutn = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'forward'+'.mp4').read()
                        
                        #Creates KML file
                        if self.createkml(dutn,fkmlcords,base_dir,pdir,dirname,current_date,video,'forward')==1 :
     
                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"
                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.mp4')
                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_forward.kml')
                    #os.system('rm -r '+base_dir+pdir+dirname+'/cropped/forward/')

                        
                
                if (camangle=='Backward') or (camangle=='All'):
                    try:
                        
                        dutn1=0
                        #stores the duration of forward video to dutn 
                        dutn1 = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'backward'+'.mp4').read()
                        
                        #Creates KML file
                        if self.createkml(dutn1,bkmlcords,base_dir,pdir,dirname,current_date,video,'backward')==1 :
                            
                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"

                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.mp4')
                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_backward.kml')
                   # os.system('rm -r '+base_dir+pdir+dirname+'/cropped/backward/')


                if (camangle=='Left') or (camangle=='All'):
                    try:
                            
                        dutn2=0 
                        #stores the duration of forward video to dutn 
                        dutn2 = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'left'+'.mp4').read()
                            
                        #Creates KML file
                        if self.createkml(dutn2,lkmlcords,base_dir,pdir,dirname,current_date,video,'left')==1 :
                         
                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"
                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.mp4')
                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_left.kml')
                    #os.system('rm -r '+base_dir+pdir+dirname+'/cropped/left/')



                if (camangle=='Right') or (camangle=='All'):
                    try:
                        dutn3=0
                        #stores the duration of forward video to dutn 
                        dutn3 = os.popen('mediainfo --Inform="Video;%Duration%" '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_'+'right'+'.mp4').read()
                        
                        #Creates KML file
                        if self.createkml(dutn3,rkmlcords,base_dir,pdir,dirname,current_date,video,'right')==1 :
                                

                            #Uploads kml to s3
                            os.system('AWS_ACCESS_KEY_ID='+aws_key+' AWS_SECRET_ACCESS_KEY='+aws_secret+' aws s3 cp '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.kml '+api_url+env+'/'+routename+'/ --acl public-read-write')
                        else:
                            print "Kml bad"
                    except:
                        print "No Cords received!"
                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.mp4')
                    #os.system('rm -r '+base_dir+pdir+dirname+'/'+current_date+'_'+video+'_right.kml')
                    #os.system('rm -r '+base_dir+pdir+dirname+'/cropped/right/')


                    
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                sql28 = 'UPDATE routes_progress SET progress="99% Completed ( Uploading KML to s3 ).",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mysql_post(sql28)

                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                sql29 = 'UPDATE routes_progress SET progress="Generation completed.",min="'+currentmin+'" WHERE route_id='+routename+' AND direction="'+sqldir+'" AND view="'+camangle+'" AND resolution="'+ores+'" AND environment="'+env+'"'
                mysql_post(sql29)

                return routename

    def calculate_initial_compass_bearing(self,pointA, pointB):
        try:
            if (type(pointA) != tuple) or (type(pointB) != tuple):
                raise TypeError("Only tuples are supported as arguments")

            lat1 = math.radians(pointA[0])
            lat2 = math.radians(pointB[0])

            diffLong = math.radians(pointB[1] - pointA[1])

            x = math.sin(diffLong) * math.cos(lat2)
            y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                    * math.cos(lat2) * math.cos(diffLong))

            initial_bearing = math.atan2(x, y)
            initial_bearing = math.degrees(initial_bearing)
            compass_bearing = (initial_bearing + 360) % 360
            return compass_bearing
        except:
            print "Error - Bearing Calculation"

    def cropfunc(self,b1,p1,d1,c1,res,kmldata):
        """
        Crops the images present in original folder and stores it in cropped folder
    
        b1 : Base directory
        p1 : Project directory
        d1 : Video directory
        c1 : View
        """
        tempkml=list()
        del tempkml[:]
        try:
            cam = c1.lower() # Converts all the characters of a string into lowercase
            
            #Gets the number of files present in the original folder
            path, dirs, files = next(os.walk(b1+p1+d1+"/original/"+cam+"/"))
            file_count = len(files)
            
            i=0
            m=0
            cropval = (res*280)/1280
            while (i!=file_count-1):
                try:
                    # Crops the images and stores it in cropped folder using ffmpeg
                    os.system('/usr/bin/ffmpeg -y -i '+b1+p1+d1+'/original/'+cam+'/'+str(i)+'.jpg'+' -vf "crop=in_w:in_h-'+str(cropval)+'" -loglevel quiet '+b1+p1+d1+'/cropped/'+cam+'/'+str(m)+'_cropped.jpg')
                    tempkml.append(kmldata[i])
                    # Removes the image in original folder to save storage space
                    os.system('rm '+b1+p1+d1+'/original/'+cam+'/'+str(i)+'.jpg')
                    i=i+1 #Increments the file number
                    m=m+1
                except:
                    print "SKIPPED AN IMAGE"
                    i=i+1
                    pass                        
                
        except:
            print "Error - cropfunc" 

        return tempkml
    
    def firedata(self,rId,dId,br,pr,sqlid,camid,ev):
        '''
        Gets coordinates from firebase,interpolates them 
        using geocords() and will then be passed through Snap To Roads

        rId : Route id
        dId : Direction
        br : Base directory
        pr : Project directory
         
        returns a list of snapped coordinates
        '''
        if dId == 'Northbound' or dId == 'Westbound':
            dId='a'
        elif dId == 'Southbound' or dId == 'Eastbound':
            dId='b'
        import json
        geopts=0
        fb_creds = getattr(settings, "FBC_"+ev.upper()+"", None)
        
        fb = firebase.FirebaseApplication(fb_creds, None) # Configure firebase
        
        data=list(); 
        fdata=list();
        del data[:]
        del fdata[:]

        #Sotres coordinates from firebase into geopts
        geopts = fb.get('/route-details-original/'+rId+'/'+dId+'/videoGeoPoints', None)
        
        if(geopts==None):
            print "No coordinates for : "+str(rId)+" Direction : "+str(dId)
            print threading.current_thread()
            return 0
        if(len(geopts)>0):
            print "Successfully received coordinates of route : "+str(rId)+" Direction : "+str(dId)
        
        for k in range(0,len(geopts)):
            try:
                g1=str(geopts[k]).replace(" ","").replace("{","").replace("}","").replace("u'","").split(",")
                lt = g1[0].split(":")
                ln = g1[1].split(":")
                data.append(str(lt[1])+','+str(ln[1]))
            except:
                print "Error Null value"
        return data

   

    def grabimage(self,data,angle,res,br,pr,dr,path,fno):
        ''' 
        Downloads the image using google street view api
         
        data : coordinates
        angle : heading angle
        resln : resolution
        br : base directory 
        pr : project directory
        dr : video directory
        path : view
        fno : file number

        '''
        try:
            if angle>360:
                angle=angle-360
            resval = (res*720)/1280
            cropval = (res-resval)/2
            params = [{
              'size': str(res)+'x'+str(resval+cropval), # max 2048x2048 pixels
              'location': data,
              'heading': angle,
              'pitch': '0.0',
              'fov':'70',
              'source':'outdoor',
              'range':'50',
              'key': google_key
            }]
            results = google_streetview.api.results(params)
            results.download_links(br+pr+dr+"/original/"+path+"/",str(fno))
                
        except:
            print "Error - grabimage"
   
    def createkml(self,timeinmsec,data,base,pi,di,cd,video,angname):
        '''
        Creates kml wrt video duration
        
        timeinsec : video duration
        data : kml coordinates 
        base : Base directory
        pi : Project directory
        di : Video directory
        video : view
        
        *Number of coordinates = Number of frames

        returns 1 if kml is successfully created
        
        '''
        try:
            time=0;
            tme=1;

            #Gets current date and time
            now = datetime.datetime.now()
            
            #time= (video duration in seconds) / (number of coordinates)
            time=(float(timeinmsec)/1000)/(len(data))
            
            f = open(base+pi+di+"/"+cd+"_"+video+"_"+angname+".kml", "w+")
            t = open(base+pi+di+"/"+cd+"_"+video+"_"+angname+"_test.txt", "w+")
            f.write("""<?xml version="1.0" encoding="UTF-8"?> <kml xmlns="http://www.opengis.net/kml/2.2">\n""")
            f.write("<Document>")
            print "NO OF COORDINATES IN KML = ",len(data),angname
            
            for i in range(0,len(data)):
                try:
                    a = data[i].split(',')
                    a3 = a[-1].split(' ')
                    t.write('\n\n https://maps.googleapis.com/maps/api/streetview?size=1280x1000&location='+a[0]+','+a3[-1]+'&heading=0&pitch=0&key='+google_key+' '+str(datetime.timedelta(seconds=int(tme)))+' '+str(i))
                    f.write('\n <SchemaData>')
                    f.write('\n   <SimpleData name="Lat">'+a[0]+'</SimpleData>')
                    f.write('\n   <SimpleData name="Lon">'+a3[-1]+'</SimpleData>')
                    f.write('\n   <SimpleData name="UTC_Date">'+str(now.day)+'/'+str(now.month)+'/'+str(now.year)+'</SimpleData>')
                    f.write('\n   <SimpleData name="UTC_Time">'+str(datetime.timedelta(seconds=int(tme)))+'</SimpleData>')
                    f.write('\n </SchemaData>')
                    tme=tme+time
                except:
                    print "Error writing to kml"
                    pass
            f.write("\n</Document>")
            f.close()
            t.close()
            print "NO OF COORDINATES ADDED TO KML = ",i,angname
            print "KML file created!"
            return 1
        except:
            print "Error - createkml"
   
class generate :
    def routedown(self,routeid):
        '''
        Creates an object for each direction
        and calls download() in class Google

        '''
        Route=['Arrayname','Route_ID','Direction','View','Resolution','environment'] # Defined the list

        Route[0]=routeid[0]
        Route[1]=routeid[1]
        Route[2]=routeid[2]
        Route[3]=routeid[3]
        Route[4]=routeid[4]
        Route[5]=routeid[5]
        
        
        if (routeid[2]=='both'):
            Route[2]='a'
            google = Google()
            google.download(Route)
            Route[2]='b'
            g1 = Google()
            g1.download(Route)
        else:
            google = Google()
            google.download(Route)
            
    

class index(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'base.html', context=None)
    def post(self, request):
        if request.body != '':
            
            ''' 
            Creates a thread on each request
            request.body : String which contains the Route_id , Direction and View  
            '''
 
            routes=list() # Created a list to store the route id direction and view 
            gen_flag = list()
            del routes[:] # Empty the contents of the list 
            
            routes=['Arrayname','Route_ID','Direction','View','Resolution','environment'] # Defined the list
            #request.body : ["rid","10 - Santa Clara Transit to Metro Airport","West","All"]
            d1=request.body.replace('"',"").replace("[","").replace("]","").split(',') # Strips away all the unwanted characters from the above string 
            #d1 : [rid,10 - Santa Clara Transit to Metro Airport,West,All] 
            d2 = d1[1].split('-')
            #Splits "10 - Santa Clara Transit to Metro Airport" to two elements "10 " and " Santa Clara Transit to Metro Airport"
            ores = d1[4]
            env = d1[5]
            aws_key = getattr(settings, "AWS_"+env.upper()+"_KEY", None)
            aws_secret = getattr(settings, "AWS_"+env.upper()+"_KEY", None)
            #print aws_key+" AWS "+aws_secret
            resolutions=["High","Low"]
#--------------------------------------------------------MANUAL DOWNLOAD-------------------------------------------------------------------
            
            if (d1[0]=="rid"):
                #d2[0] = "10 "
               


                '''Set the direction to a if string is West and b if string is East'''
                
                routes[0]="rid" #Changes the 1st element of the array to rid
                routes[1]=d2[0].replace(" ","") #Removes the white space in "10 " and stores it to the 2nd element of the array which is route_id
                routes[2]=d1[2] # Stores the direction
                routes[3]=d1[3] #Stores the View to 4th element of the array which is camangle
                routes[4]=ores
                routes[5]=env
                ''' calls routedown function in class generate as a thread '''
                if ores!='All':
                    thd = threading.Thread(target=generate().routedown,args=(routes,))
                    thd.setDaemon(True) # sets the thread as daemon thread
                    thd.start() # starts the thread
                
                if ores=='All':
                    routes[4]='High'
                    thd = threading.Thread(target=generate().routedown,args=(routes,))
                    thd.setDaemon(True) # sets the thread as daemon thread
                    thd.start() # starts the thread
                    time.sleep(5)
                    routes[4]='Low'
                    thd1 = threading.Thread(target=generate().routedown,args=(routes,))
                    thd1.setDaemon(True) # sets the thread as daemon thread
                    thd1.start() # starts the thread
                

                return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')
#--------------------------------------------------------------AUTOMATED DOWNLOAD--------------------------------------------------------

            # if (d1[0]=="rid"):
            #     # #d2[0] = "10 "
               


            #     # '''Set the direction to a if string is West and b if string is East'''
                
            #     # routes[0]="rid" #Changes the 1st element of the array to rid
            #     # routes[1]=d2[0].replace(" ","") #Removes the white space in "10 " and stores it to the 2nd element of the array which is route_id
            #     # routes[2]=d1[2] # Stores the direction
            #     # routes[3]=d1[3] #Stores the View to 4th element of the array which is camangle
            #     # routes[4]=ores
            #     # routes[5]=env
            #     # ''' calls routedown function in class generate as a thread '''
            #     # if ores!='All':
            #     #     thd = threading.Thread(target=generate().routedown,args=(routes,))
            #     #     thd.setDaemon(True) # sets the thread as daemon thread
            #     #     thd.start() # starts the thread
                
            #     # if ores=='All':
            #     #     routes[4]='High'
            #     #     thd = threading.Thread(target=generate().routedown,args=(routes,))
            #     #     thd.setDaemon(True) # sets the thread as daemon thread
            #     #     thd.start() # starts the thread
            #     #     time.sleep(5)
            #     #     routes[4]='Low'
            #     #     thd1 = threading.Thread(target=generate().routedown,args=(routes,))
            #     #     thd1.setDaemon(True) # sets the thread as daemon thread
            #     #     thd1.start() # starts the thread
            #     dirarr=['a','b']
                
            #     routelist=[32,34,35,37,39,40,42,45,46,47,48,49,52,53,54,55,57,58,60,61,62,63,64,65,66,68,70,71,72,73,77,81,82,88,89,101,102,103,104,120,121,122,140,168,180,181,182,185,200,304,321,323,328,330,522,822,823,824,825,826,827,828,831] #route list

            #     routes[0]='rid'
            #     routes[3]='All'
            #     routes[5]='Production'
            #     while len(routelist)>5:
            #         routes[1]=str(routelist[0])
                    
            #         routes[2]='a'
            #         routes[4]='High'
            #         print routes
            #         thd = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd.setDaemon(True) # sets the thread as daemon thread
            #         thd.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[4]='Low'
            #         print routes
            #         thd1 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd1.setDaemon(True) # sets the thread as daemon thread
            #         thd1.start() # starts the thread
            #         time.sleep(5)

            #         routes[2]='b'
            #         routes[4]='High'
            #         print routes
            #         thd2 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd2.setDaemon(True) # sets the thread as daemon thread
            #         thd2.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[4]='Low'
            #         print routes
            #         thd3 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd3.setDaemon(True) # sets the thread as daemon thread
            #         thd3.start() # starts the thread
            #         time.sleep(5)
                    
            #         routelist.pop(0)
                    
            #         routes[1]=str(routelist[0])
                    
            #         routes[2]='a'
            #         routes[4]='High'
            #         print routes
            #         thd4 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd4.setDaemon(True) # sets the thread as daemon thread
            #         thd4.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[4]='Low'
            #         print routes
            #         thd5 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd5.setDaemon(True) # sets the thread as daemon thread
            #         thd5.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[2]='b'
            #         routes[4]='High'
            #         print routes
            #         thd6 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd6.setDaemon(True) # sets the thread as daemon thread
            #         thd6.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[4]='Low'
            #         print routes
            #         thd7 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd7.setDaemon(True) # sets the thread as daemon thread
            #         thd7.start() # starts the thread
            #         time.sleep(5)
                    
            #         routelist.pop(0)
                    
            #         routes[1]=str(routelist[0])
                    
            #         routes[2]='a'
            #         routes[4]='High'
            #         print routes
            #         thd8 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd8.setDaemon(True) # sets the thread as daemon thread
            #         thd8.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[4]='Low'
            #         print routes
            #         thd9 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd9.setDaemon(True) # sets the thread as daemon thread
            #         thd9.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[2]='b'
            #         routes[4]='High'
            #         print routes
            #         thd10 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd10.setDaemon(True) # sets the thread as daemon thread
            #         thd10.start() # starts the thread
            #         time.sleep(5)
                    
            #         routes[4]='Low'
            #         print routes
            #         thd11 = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd11.setDaemon(True) # sets the thread as daemon thread
            #         thd11.start() # starts the thread
            #         time.sleep(5)
                    
            #         routelist.pop(0)
                    
            #         thd1.join()
            #         thd2.join()
            #         thd3.join()
            #         thd4.join()
            #         thd5.join()
            #         thd6.join()
            #         thd7.join()
            #         thd8.join()
            #         thd9.join()
            #         thd10.join()
            #         thd11.join()
            #     i=0
            #     thd=list();
            #     thd = [None] * 50
            #     while len(routelist)!=0:
            #         routes[1]=str(routelist[0])
            #         routes[2]='a'
            #         routes[4]='High'
            #         thd[i] = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd[i].setDaemon(True) # sets the thread as daemon thread
            #         thd[i].start() # starts the thread
            #         i=i+1
            #         time.sleep(5)
            #         routes[4]='Low'
            #         thd[i] = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd[i].setDaemon(True) # sets the thread as daemon thread
            #         thd[i].start() # starts the thread
            #         i=i+1
            #         time.sleep(5)
            #         routes[2]='b'
            #         routes[4]='High'
            #         thd[i] = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd[i].setDaemon(True) # sets the thread as daemon thread
            #         thd[i].start() # starts the thread
            #         i=i+1
            #         time.sleep(5)
            #         routes[4]='Low'
            #         thd[i] = threading.Thread(target=generate().routedown,args=(routes,))
            #         thd[i].setDaemon(True) # sets the thread as daemon thread
            #         thd[i].start() # starts the thread
            #         routelist.pop(0)
            #         i=i+1
            #         time.sleep(5)

            #     return HttpResponse(json.dumps({'status': 'success'}), content_type='application/json')
#-----------------------------------------------------------------------------------------------------------------------------
            elif (d1[0]=="dbinfo"):
                stats=list();
                pstats=list();
                cstats=list();
                ctime=list();
                del stats[:];
                del pstats[:];
                del cstats[:];
                ptime=0
                stime=0
                

                sql33 = 'SELECT * FROM routes_progress WHERE route_id='+d2[0].replace(" ","")+' AND direction="'+d1[2]+'" AND view="'+d1[3]+'" AND environment="'+env+'"'
                cstats=mysql_get(sql33)
                currentmin = str(os.popen('date +"%M"').read()).replace("\n","")
                try:    
                    for k in range(0,2):
                        ptime=(int(currentmin)-int(cstats[k][5]))
                        if(ptime<0):
                            ptime=ptime+60
                    
                        if (ptime>15):
                            sql34 = 'UPDATE routes_progress SET gen_status=1 WHERE route_id='+str(cstats[k][1])+' AND direction="'+cstats[k][2]+'" AND view="'+cstats[k][3]+'" AND resolution="'+cstats[k][7]+'" AND environment="'+cstats[k][8]+'"'
                            mysql_post(sql34)
                            pass
                        if cstats:
                            if cstats[k][4]=="Generation completed.":
                                stats.append("Time")
                                if cstats[k][3]=='All':
                                    vw="Forward"
                                else:
                                    vw=cstats[k][3]
                                sql35 = 'SELECT date_time FROM routes_log WHERE route_id='+str(cstats[k][1])+' AND direction="'+cstats[k][2]+'" AND type="VIDEO_'+vw+'" AND resolution="'+cstats[k][7]+'" AND environment="'+cstats[k][8]+'" ORDER BY id DESC LIMIT 1'
                                del ctime[:]    
                                ctime.append(mysql_get(sql35))
                                stats.append(ctime[0][0][0])
                            else:
                                if cstats[k][4]==None:
                                    cstats[k][4]="Starting video generation."
                                stats.append("Progress")
                                stats.append(cstats[k])
                except:
                        pass

                sql33 = 'SELECT * FROM routes_progress WHERE progress !="Generation completed." '
                pstats=mysql_get(sql33)
                stats.insert(4,[pstats])
                if len(stats)>2:
                    return HttpResponse(json.dumps(stats))
                else:
                    stats.insert(0,"no_data_in_db")
                    stats.insert(1,"no_data_in_db")
                    stats.insert(2,"no_data_in_db")
                    stats.insert(3,"no_data_in_db")
                    stats.insert(4,[pstats])
                    return HttpResponse(json.dumps(stats))

