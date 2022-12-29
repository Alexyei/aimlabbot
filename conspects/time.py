# In source of this repositoty used: time.time_ns() / 1000000) / 1000)%60
# Неопонятно зачем здесь %60 (возможно взято отсюда: https://overcoder.net/q/37667/каков-наилучший-способ-повторно-выполнять-функцию-каждые-x-секунд-в-python#1148003)


import time

t1 = time.time()
t2 = time.perf_counter_ns()/1000000/1000
t3 = time.perf_counter()
# print(t1)
# print(time.perf_counter_ns())
print(time.time())
print((time.time_ns()/1000000)/1000)
print()
time.sleep(70)

print(time.time() - t1)
print((time.time() - t1)%60)
print((time.time()%60 - t1%60))
print()
print(time.perf_counter_ns()/1000000/1000 - t2)
print((time.perf_counter_ns()/1000000/1000 - t2)%60)
print(((time.perf_counter_ns()/1000000/1000)%60 - t2%60))
print()
print(time.perf_counter() - t3)
print((time.perf_counter() - t3)%60)
print((time.perf_counter()%60 - t3%60))
print()

# OUTPUT
# 1672229352.6415677
# 1672229352.6415982
#
# 70.01879453659058
# 10.018843412399292
# 10.018867492675781
#
# 70.01888145900003
# 10.018889637000001
# 10.01889282800002
#
# 70.01889627400001
# 10.018899016000006
# 10.01891492300004

