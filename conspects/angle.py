
# Online Python - IDE, Editor, Compiler, Interpreter
# https://www.calc.ru/raschet-treugolnika/abdb016559847f6c291276ee3b257fdd
# https://www.calc.ru/raschet-treugolnika/58fed1694cb696d7d3fbd43ae829fd16
import math

fov_h = 106
AB = fov_d = 10
angle_a = fov_h/2
rel = 2/5
# hypotenuse
AC = fov_d/math.cos(math.radians(angle_a))
print("AC: ",AC)
BC = math.sqrt(AC**2-AB**2)
print("BC: ",BC)
BE = rel*BC
tan_a = BE/AB
angle_a = math.degrees(math.atan(tan_a))
print("Angle A:",angle_a)
print(fov_d/math.cos(math.radians(angle_a)))
print(math.degrees(math.atan(math.sqrt(3))))