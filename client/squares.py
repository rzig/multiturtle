import multiturtle as turtle
import time

turtle.Screen().setup()

def square(tt, s):
    tt.forward(s)
    tt.left(90)
    tt.forward(s)
    tt.left(90)
    tt.forward(s)
    tt.left(90)
    tt.forward(s)
    tt.left(90)

time.sleep(10)

turtle.connect("41KN1", "circles")

# time.sleep(1)

time.sleep(10)

t = turtle.Turtle()
t.color("green", "orange")

rad = 10
while rad <= 100:
    square(t, rad)
    rad += 10

turtle.Screen().exitonclick()
turtle.disconnect()