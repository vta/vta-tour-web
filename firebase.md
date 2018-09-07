STEP-1: Please login to firebase.google.com, GoTo Console, then Click Add Project. Give some name project name, Accept terms and click Create Project.

STEP-2: GoTo Github and copy the Git UTL. Open Terminal and perform all the commands below.

Start by executing git clone in terminal to create the repo (git-folder url name). It should be:

git clone https://github.com/vta/vta-tour-web.git

It should create a directory in local called vta-tour-web. Then do “cd vta-tour-web” to be in the root of the directory.

STEP-3: Setup firebase and required modules

1) Create .firebaserc file in root folder with following content (need to change as per project id change). It is best to use Sublime text or some text editor for this. (File should contain the following six lines). Replace (new server name) with name of the server you created in STEP-1. example: vtatest1-5882f.
{
 "projects": {
   "staging": “(new server name)",
   "default": "(new server name)"
 }
}
(In root folder, execute the following commands)
2) curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh | bash
3) nvm install v8
4) nvm use v8
5) npm install bower -g
6) npm install gulp -g

(In web folder)
7) npm install -g @polymer/gen-typescript-declarations
8) npm install
9) bower install

(In backoffice folder)
10) bower install (run in backoffice folder)
11) npm install (in backoffice folder)

(Switch back to root folder)
12) npm install firebase -g (install firebase)
13) npm install -g firebase-tools
14) firebase login --no-localhost
15) firebase use --add

(In functions folder)
16) npm install

17) Go to  Firebase website and open Project - Click Database on left (Create Database) - Locked mode.
Change to realtime Database from dropdown above.

18) Find API key in Project settings (within Firebase.google.com website)

19) In backoffice/app/index.html, Change this line below:
<firebase-app name="vta" auth-domain="vtatest1-5882f.firebaseapp.com" database-url="https://vtatest1-5882f.firebaseio.com" api-key="AIzaSyALqCogus7yIJJ0OE48RwBtmteqybWvZ6g"></firebase-app>

20) In web/app/index.html, change line below:
<firebase-app name="vta" auth-domain="vtatest1-5882f.firebaseapp.com" database-url="https://vtatest1-5882f.firebaseio.com" api-key="AIzaSyALqCogus7yIJJ0OE48RwBtmteqybWvZ6g"></firebase-app>

21) in web/app/elements/config-store/config-store.html -  add google maps api key for prod
(Use latest google api key)

(Switch back to root folder)
22) sh ./build
23)npm install -g firebase-export
24) mkdir data

25) firebase use default
26) firebase serve (this is just to confirm everything was installed fine)
27)  firebase deploy

STEP-4: Create Backoffice User

Please login to firebase.google.com, GoTo Console, then click the new Firebase instance that was created and create backoffice username/password.

STEP-5: Update Data

1) import stops and routes -> Batch import
2) Import JSON table as "route-details-resources” using Firebase UI
3) Run batch update (all video and kml + stops data will be set)
4) Import amenities
5) Point mobile apps to the new server
