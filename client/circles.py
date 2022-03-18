import multiturtle as turtle
import time

turtle.Screen().setup()

turtle.connect("4QA8T", "circles")

# time.sleep(1)

time.sleep(10)

t = turtle.Turtle()
t.color("red", "blue")

rad = 10
while rad <= 100:
    t.circle(rad)
    rad += 10

turtle.Screen().exitonclick()
turtle.disconnect()