# lambda is an anonymous function - does not use a name unless defined
# lambda arg1, arg2, .... : expression 

# sum lambda example
sum = lambda x, y: x + y
print("Sum :", sum(4, 5))

# conditional lambda example
can_vote = lambda age: True if age >= 18 else False
print("Can Vote :", can_vote(19))

# create list of functions
powerList = [lambda x: x**2,
			 lambda x: x**3,
			 lambda x: x**4]
			 
# call func list
for func in powerList:
	print(func(4))

