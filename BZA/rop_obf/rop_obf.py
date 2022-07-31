from z3 import *
s=Solver()
array=[BitVec("array%i"%i,32) for i in range(6)]

s.add(array[0]^0x83==0x87)
s.add(array[1]^0x36==0x3e)
s.add(array[2]^0x9d==0x92)
s.add(array[3]^0xcd==0xdd)
s.add(array[4]^0xec==0xfb)
s.add(array[5]^0xf6==0xdc)

if s.check()==sat:
    flag=s.model()
    for i in range(6):
        ans=((flag[array[i]]))
        print(ans)

