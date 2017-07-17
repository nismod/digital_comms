import random

int_list = []

for i in range(1, 100):
	int_list.append(i)

final_list = []

randList = list(random.randint(1, 1001) for i in range(100))
print(list(filter((lambda x: x % 9 == 0), randList)))


