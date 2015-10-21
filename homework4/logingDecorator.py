__author__ = 'Demidov'

def logging(function, log_file):
    def wrap(*args, **kwargs):
        res = function(*args, **kwargs)
        import logging
        logging.basicConfig(filename = log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info((function.__name__, args, kwargs))
        return res
    return wrap

def ater(a):
    print(a)


logging(ater, 'a.txt')(2)











