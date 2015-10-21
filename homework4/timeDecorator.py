__author__ = 'Demidov'

def qsort(list):
    return [] if list == [] else qsort([x for x in list[1:] if x < list[0]]) + [list[0]] + qsort([x for x in list[1:] if x >= list[0]])

def decorator(function):
    def wrap(*args, **kwargs):
        import time
        start_time = time.clock()

        result_function = function(*args, **kwargs)

        print((time.clock() - start_time) * 1000)
        return result_function

    return wrap

list =[1, 2, 5, 2, 1]

print(decorator(qsort)(list))












