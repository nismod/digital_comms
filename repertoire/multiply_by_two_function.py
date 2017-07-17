#basic multiply function
def multiply_by_2(num):
	return num * 2
	
times_two = multiply_by_2

print("6 * 2 =", times_two(6))

#use multiple functions
def do_math(func, num):
	return func(num)
	
print("10 * 2=", do_math(multiply_by_2, 10))

