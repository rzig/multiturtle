import multiturtle as turtle
import time

def square(tt, s):
    tt.forward(s)
    tt.left(90)
    tt.forward(s)
    tt.left(90)
    tt.forward(s)
    tt.left(90)
    tt.forward(s)
    tt.left(90)

turtle.connect("LTB1L", "squares")
turtle.Screen().setup()

t = turtle.Turtle()
t.color("green", "orange")

rad = 10
while rad <= 100:
    square(t, rad)
    rad += 10

turtle.Screen().exitonclick()
turtle.disconnect()