#dynamically created function, and return a function from a function
#basic multiply function
def multiply_by_2(num):
	return num * 2
	
times_two = multiply_by_2

def get_func_multiply_by_num(num):

	def mult_by(value):
		return num * value
	
	return mult_by
	
generated_func = get_func_multiply_by_num(5)

print("5 * 8 =", generated_func(8))

#create list of functions
listOfFuncs= [times_two, generated_func]

print("5 * 9 =", listOfFuncs[1](9))