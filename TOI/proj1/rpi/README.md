
# Installation
  * Setup RPi access-point(AP) based on your linux installation there and install docker there
  * In our case we used the raspbian and this [tutorial](https://thepi.io/how-to-use-your-raspberry-pi-as-a-wireless-access-point/) to setup the AP 
  * The RPi app can be run via the docker with command 
    `docker build -t toi_rpi .` 
    `docker run -it -p 5000:5000 toi_rpi ` 
  * Now the app should be running on the port 5000
  
  
