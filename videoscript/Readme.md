# VTA Tour Video Generation Script #

## What is this repository for? ##

* Repository for **VTA Tour Video Generation Script** website.
* Version: 1.0

### Requirements ###
* Python 2.7.12
* Apache/2.4.18
* Mysql 5.7.23
* Django 2.1

## How to setup? ##

1.  Install Apache HTTP server

2.  Install MySQL and Python 2.7

3.  Create a Database “VTA”

4.  Run the following SQL query in the database

      https://s3-us-west-1.amazonaws.com/vta-tour-rtmp/database-init/vta-init-db.sql

5.  Install packages

      Open the folder containing requirements.txt in terminal and run the following   command

      sudo pip install -r requirements.txt

6.  Go to the "web" folder /var/www/html/

7.  Clone the repository

8.  Update credentials in settings file - Details are in the file.

      Open Settings.py (Location : vta/vta/settings.py)

      Enter the authentication credentials in vta credentials section in settings.py

9.  Set project path

      Open Manage.py (Location: vta/manage.py)

      Enter the project path

10. Google Streetview API

      Replace api.py in “Google_Streetview” in python folder (/usr/local/lib/python2.7/ either dist-packages/site-packages) with

      https://github.com/vta/vta-tour-web/tree/master/videoscript/google_api/api.py

11. Configure apache server.

      Create conf file vta.conf with following content and load this conf for Apache. (path to create file: /etc/apache2/sites-enabled/)


	WSGIPythonHome /var/www/html/vta-tour-web/videoscript/venv/  
	<VirtualHost *:80>  
	ServerAdmin admin@vtatour.com  
	KeepAlive On  
	TimeOut 180000  
	KeepAliveTimeout 90000  
	WSGIDaemonProcess vta python-path=/usr/local/lib/python2.7/dist-packages  
	WSGIProcessGroup vta  
	WSGIApplicationGroup %{GLOBAL}  
	Alias /static/ /var/www/html/vta-tour-web/videoscript/static/  
	<Directory /home/crowdplat/vta/static>  
	    Require all granted
	</Directory>  
	WSGIScriptAlias / /var/www/html/vta-tour-web/videoscript/vta/wsgi.py  
	<Directory /home/crowdplat/vta/>  
	    <Files wsgi.py>  
	       Require all granted
	    </Files>  
	    SetEnvIfNoCase Host ip-172-31-15-203.us-west-1.compute.internal VALID_HOST  
	    Require env VALID_HOST  
	    Options
	</Directory>
	</VirtualHost>

## Important topics ##

### Base Technology Stack ###
* Python/Django/Mysql/Firebase (Backend)
* HTML/Jquery (Frontend)

### Git branch model ###
The Git branch model that will be followed is the one proposed by GitFlow and documented [here](http://nvie.com/posts/a-successful-git-branching-model/).

