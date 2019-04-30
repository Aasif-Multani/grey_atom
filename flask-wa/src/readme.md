### How to run the flask webapp

#### Prerequisite 
#### Anaconda -
https://www.digitalocean.com/community/tutorials/how-to-install-anaconda-on-ubuntu-18-04-quickstart 
#### MongoDB - 
https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-16-04


run the following commands in your terminal 

```
$ git clone <repo url> # if doing it for the first time else just git pull 
$ cd flask-wa
$ conda create -n greyatom python=3
$ conda activate greyatom
$ cd src 
$ pip install -r requirements.txt
$ python initialise.py # used to initialise all the datasets in mongodb and
other processing when sever starts. (Make Sure MongoDB is there and running as service)
$ python server.py
``` 

visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to view the webapp!
