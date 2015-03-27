RB-2: my second bot-car with a lot of improvements on very much lessons learned.  
Credentials:
Dawn Robotics [http://www.dawnrobotics.co.uk/]: Tornado, WebSockets, camera streamer and Dagu mini driver
Adrian Rosebrock: [http://www.pyimagesearch.com]: Python openCV 
Samuel Matos  [http://roboticssamy.blogspot.nl/]: epic inspirations
Change log:
The chassis: the Dagu magician chassis is great to start with. For the purpose I had in mind, I needed good control over the movements of the car. The Dagu spun and swirled too much:
-	Light weighted; adding weight strains the axis 
-	Rear caster becomes a rudder at unevenness (e.g.  a tiled floor) 
-	Hard tires slip on smooth surface (especially when adding weight and torque is needed) 
So I switched to a DF-robot frame with 4 motors and softer tires and keep the Dagu for another time (maybe as bumper car or hand following bot).   

Also the coding needed 'some' revision. The former release was too error sensitive:
-	Only worked at (very, very) low speed 
-	Often lost direction while moving even on slight changes in the light conditions
-	Dependent of ultrasonic ranging. So only works in a uncluttered environment. 

Search routine
-	A bit less dependent of light conditions
-	Just uses mask inRange and Contours
-	Use of boundingRectangle i.s.o. Moments
-	No need for error handling (M00 != 0)
-	Significant faster: on average 15 times (now 2 millSec)
-	Reduced lines of code
-	Some points to consider:
  -	Produces more positive readings (even a partial marker is a hit)
  -	A bounding box is slightly bigger than contours 

Range
-	No longer needed. Kept it in the code for near-object-detection. Played a bit with vision-ranging (also not really needed). 
Timer
-	Time.sleep() is  only sufficient for very small interrupts. Added a simple function to get timing a bit more accurate  

Moving
-	Less math needed; adjustments now based upon image changes
-	No dependency on ultrasonic ranging 
-	Fast feedback (searching & adjusting) 






