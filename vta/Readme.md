# VTA Tour Video Generation Script #

## What is this repository for? ##

* Repository for **VTA Tour Video Generation Script** website.
* Version: 1.0

### Requirements ###
* Python 2.7.12
* Apache/2.4.18
* Mysql 5.7.23
* Django 2.1
* ffmpeg 2.8.15-0
* MediaInfoLib - v0.7.82
* ImageMagick 6.8.9-9
* awscli

## How to setup? ##

1.  Install Apache HTTP server

		$ sudo apt-get install apache2 -y

2.  Install MySQL and Python 2.7
    
     #### MySQL: ####
		$ sudo apt-get update
		$ sudo apt-get install mysql-server
		$ mysql_secure_installation

    Create new mysql user:

		1. Enter mysql -u root -p in console and enter password
		2. CREATE USER 'dbuser'@'localhost' IDENTIFIED BY 'password';
		3. GRANT ALL PRIVILEGES ON * . * TO 'dbuser'@'localhost';
		4. FLUSH PRIVILEGES;
		5. SET SQL_SAFE_UPDATES = 0;
		6. CREATE database vta;

 
     #### Python: ####
        
	
		$  sudo apt update
		$  sudo apt upgrade
		$  sudo apt install python2.7 python-pip


3.  Run the following SQL query in the database

		$ mysql -u root -p vta < /var/www/html/vta/vta-init-db_test.sql

4.  Install packages

      Open the folder containing requirements.txt in terminal and run the following   command

		$ sudo pip install -r requirements.txt

5.  Go to the "web" folder /var/www/html/

6.  Clone the repository (do not skip .at end in clone command)
		
		$ git clone https://github.com/vta/vta-tour-web.git .

    Set permission to project folder

		$ sudo chmod 775 -R vta/

7.  Install following packages

		$ sudo apt-get install libapache2-mod-wsgi
		$ sudo a2enmod wsgi
		$ sudo service apache2 restart
		$ sudo apt-get install libmysqlclient-dev
		$ sudo add-apt-repository ppa:mc3man/trusty-media
		$ sudo apt-get update
		$ sudo apt-get install ffmpeg
		$ sudo apt-get install frei0r-plugins
		$ sudo apt-get install libav-tools
		$ sudo apt-get install imagemagick imagemagick-doc
		$ sudo apt-get install python-mysqldb
		$ sudo apt-get install mediainfo 
		$ sudo apt-get install x264 -y

     Create Virtual env for Django:

		$ sudo -H pip install virtualenv
		$ virtualenv venv
		$ source venv/bin/activate

8.  Configure AWS key in cli

		$ sudo apt install awscli
		$ aws configure

9.  Set project path in views.py at /var/www/html/vta/vtatour
    
	base_dir = '/var/www/html/vta' #Base directory

10.  Update credentials in settings file - Details are in the file.

      Open Settings.py (Location : vta/vta/settings.py)

      Enter the authentication credentials in vta credentials section in settings.py

11.  Set project path in manage.py at /var/www/html/vta/

       Enter the project path as "/var/www/html/vta"

12. Set project path wsgi.py at /var/www/html/vta/vta/

    sys.path.append("/var/www/html/vta")

13. Google Streetview API

      Replace api.py in “Google_Streetview” in python folder (/usr/local/lib/python2.7/dist-package) with following file

      https://github.com/vta/vta-tour-web/tree/master/videoscript/google_api/api.py

 		/var/www/html/vta/google_api$ sudo cp api.py /usr/local/lib/python2.7/dist-packages/google_streetview/

      Change the variable secret = "" with google sign in screet key

14. Configure apache server.

      Create conf file vta.conf with following content and load this conf for Apache. (path to create file: /etc/apache2/sites-available/)

		
```
	DocumentRoot /var/www/html/vta
	WSGIPythonHome /var/www/html/venv/
	<VirtualHost *:80>
	ServerAdmin admin@vtatour.com
	KeepAlive On
	TimeOut 180000
	KeepAliveTimeout 90000
	WSGIDaemonProcess vta python-path=/usr/local/lib/python2.7/dist-packages
	WSGIProcessGroup vta
	WSGIApplicationGroup %{GLOBAL}
	Alias /static/ /var/www/html/vta/static/
	<Directory /var/www/html/vta/static>
	    Require all granted
	</Directory>
	WSGIScriptAlias / /var/www/html/vta/vta/wsgi.py
	<Directory /var/www/html/vta/>
	    <Files wsgi.py>
	       Require all granted
	    </Files>
	    SetEnvIfNoCase Host ip-52-8-150-189.us-west-1.compute.internal VALID_HOST
	    Require env VALID_HOST
	    Options
	</Directory>
	</VirtualHost>

```
	Disable default config of apache:
	/etc/apache2/sites-available$ sudo a2dissite 000-default.conf

	Enable vta config of apache:
	/etc/apache2/sites-available$ sudo a2ensite vta.conf

	Check if new config is loaded:
	$apachectl -t -D DUMP_VHOSTS

## Important topics ##

### Base Technology Stack ###
* Python/Django/Mysql/Firebase (Backend)
* HTML/Jquery (Frontend)

### Git branch model ###
The Git branch model that will be followed is the one proposed by GitFlow and documented [here](http://nvie.com/posts/a-successful-git-branching-model/).
