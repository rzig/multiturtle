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

turtle.connect("4QA8T", "squares")

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