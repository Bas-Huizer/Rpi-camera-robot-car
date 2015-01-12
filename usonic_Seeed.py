#! /usr/bin/python

# Example how to use the Seeed Studio 3 pins ultrasonic reader 
#
# The routine first searches for 2 readings with a difference < 10%
# Then it searches for [x_times] other readings in the same range and calculates the average
# (Basic and straight forward coding)
#
# Don't reduce the sleeping time in the routine: a faster loop results in more failures (and takes longer in the end as well)
# Getting 3 readings in range, takes around 0.3 seconds
#
# Note: For obvious reasons, don't use less than 3 readings
# Note: By logic one could take 3 readings and drop the one most out of range.
#       Trying that I couldn' increase speed and recieved worse results
# Note: The transducers have a wide angle of sensitivity. In a cluttered environment one might get shorter readings and/or more scattering
# Note: Measurements below 2 cm will give strange results anyhow

# Initializing
import time
import argparse             # Working on the Dawn Robotics Pi-camera-bot through the robots webserver
import py_websockets_bot 
import py_websockets_bot.mini_driver
import py_websockets_bot.robot_config

def get_range ():
    bot.update()
    status_dict, read_time = bot.get_robot_status_dict()
    sensor_dict = status_dict[ "sensors" ]
    data = sensor_dict[ "ultrasonic" ][ "data" ]
    distance = data
    return distance
def get_average_range(x_times):
    start_time = time.time ()
    count = 1
    reading_count = 0
    distance_cum = 0
    while count <= x_times:
        reading_count += 1
        distance_read = get_range()
        if count == 1:
            distance_save = distance_read
        else:
            if count == 2:
                if distance_read > (1.1*distance_save) or distance_read < (0.9*distance_save):
                    print "First readings out of range (10%)", distance_save, "and", distance_read, "; both readings ignored"
                    distance_cum = 0
                    count = 1    
        if distance_read > (1.1*distance_save) or distance_read < (0.9*distance_save):
            if count > 2:
                print "Reading", reading_count, "Unexpected value:", distance_read, "; reading ignored"
        else:        
            distance_cum += distance_read
            print "Reading", reading_count, "Count #" ,count, "Value", distance_read, "cm,Total counted", distance_cum, "cm"
            count += 1
        time.sleep (0.03)
    distance_avg = distance_cum / (count-1)
    print ""
    print "Average distance =", distance_avg, "cm"
    end_time = time.time()
    duration = end_time - start_time
    duration = round(duration, 1)
    print "Routine duration:", duration, "sec"
    return distance_avg
#---------------------------------------------------------------------------------------------------        
if __name__ == "__main__":

    # Set up a parser for command line arguments
    parser = argparse.ArgumentParser( "Gets sensor readings from the robot and displays them" )
    parser.add_argument( "hostname", default="localhost", nargs='?', help="The ip address of the robot" )
    args = parser.parse_args()
 
    # Connect to the robot
    #bot = py_websockets_bot.WebsocketsBot( args.hostname ) # When running a local script on the Pi
    bot = py_websockets_bot.WebsocketsBot( "192.168.42.1" ) # When running a script at a remote computer using webSockets

    # Configure the sensors on the robot
    sensorConfiguration = py_websockets_bot.mini_driver.SensorConfiguration(
        configD12=py_websockets_bot.mini_driver.PIN_FUNC_ULTRASONIC_READ, 
        configD13=py_websockets_bot.mini_driver.PIN_FUNC_INACTIVE, 
        configA0=py_websockets_bot.mini_driver.PIN_FUNC_ANALOG_READ, 
        configA1=py_websockets_bot.mini_driver.PIN_FUNC_ANALOG_READ,
        configA2=py_websockets_bot.mini_driver.PIN_FUNC_ANALOG_READ, 
        configA3=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,
        configA4=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ, 
        configA5=py_websockets_bot.mini_driver.PIN_FUNC_DIGITAL_READ,
        leftEncoderType=py_websockets_bot.mini_driver.ENCODER_TYPE_QUADRATURE, 
        rightEncoderType=py_websockets_bot.mini_driver.ENCODER_TYPE_QUADRATURE )
      
    robot_config = bot.get_robot_config()
    robot_config.miniDriverSensorConfiguration = sensorConfiguration
    bot.set_robot_config( robot_config )
        
    # Procedure: call for a range measurement # times and calculate the average
    range_readings = []
    count =1
    x_times = 10
    while count <=8:   
        range_measured = get_average_range(x_times)
        range_readings.append(range_measured)
        count += 1
        x_times -= 1
    print ""
    print "Ranges returned: ", range_readings
        
    # Disconnect from the robot
    bot.disconnect()
