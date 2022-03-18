import multiturtle as turtle
import time

turtle.Screen().setup()

turtle.connect("LTB1L", "circles")

t = turtle.Turtle()
t.color("red", "blue")

rad = 40
while rad <= 100:
    t.circle(rad)
    rad += 10

turtle.Screen().exitonclick()
turtle.disconnect()