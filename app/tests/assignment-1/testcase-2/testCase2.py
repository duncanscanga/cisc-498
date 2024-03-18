import unittest
from autograder_utils.decorators import visibility, partial_credit, output_format
import subprocess
import re
from math import floor

def check(line, error, output, penalty):
    p = re.compile(line, flags=0)
    m = p.search(output)
    if m == None:
        print(error)
        return penalty
    else:
        return 0

#takes in two diemension string array with what to look for and what to print after it
#example: inputs[0][0] is "Input a number:" inputs [1][0] is "5"
#example: inputs[0][1] is "Input another number:" inputs[1][1] is "6"
def printWithInput(inputs, output):
    output += '\n'
    x = 0
    y = 0
    word = ''
    while x < len(output):
        if output[x] == '\n':
            print(word)
            while y < len(inputs[0]):
                if inputs[0][y] == word:
                    print("\033[4;34m" + inputs[1][y] + "\033[0m")
                y += 1
            word = ''
            y = 0
        else:
            word += output[x]
        x += 1

class TestDiff(unittest.TestCase):
    def setUp(self):
        pass

    # Associated point value within GradeScope
    @partial_credit(4)
    @visibility('visible')
    @output_format('ansi')
    def test_case1(self, set_score=None):
        # Title used by Gradescope
        """Test Case 2"""

        # Create a subprocess to run the students code and with our test file
        cat = subprocess.Popen(["cat", "test2.txt"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        test = subprocess.Popen(["./assign4.out"], stdin=cat.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = test.stdout.read().strip().decode('utf-8')

        test.kill()
        cat.kill()

        # Standard unit test case with an associated error message

        inputs = [
            ["Please input the initial costs of the three trucks:", 
             "Please input the initial yearly maintenance costs of the three trucks:", 
             "Please input the project lifespan in years:"], 
             ["10000 20000 30000", 
              "1000 500 250", 
              "25"]]

        print("Output from your program:")
        printWithInput(inputs, output)

        print("\nExpected output: ")
        years = inputs[1][2]
        half = str(floor(int(years)/2))

        print("Please input the initial costs of the three trucks:\n" + 
              "\033[4;34m" + inputs[1][0] + "\033[0m" + "\n" + 
              "Please input the initial yearly maintenance costs of the three trucks:\n" + 
              "\033[4;34m" + inputs[1][1] + "\033[0m" + "\n" + 
              "Please input the project lifespan in years:\n" + 
              "\033[4;34m" + inputs[1][2] + "\033[0m" + "\n" + 

              "The cost of truck 1 after " + half + " years is $31384.28.\n" + 
              "Next year's maintenance will be $3138.43.\n" + 
              "The cost of truck 2 after " + half + " years is $30692.15.\n" + 
              "Next year's maintenance will be $1569.21.\n" + 
              "The cost of truck 3 after " + half + " years is $35346.07.\n" + 
              "Next year's maintenance will be $784.61.\n" + 
              "\nAt $30692.15, truck 2 is the best investment after " + half + " years.\n\n" +

              "The cost of truck 1 after " + years + " years is $108347.05.\n" + 
              "Next year's maintenance will be $10834.71.\n" + 
              "The cost of truck 2 after " + years + " years is $69173.53.\n" + 
              "Next year's maintenance will be $5417.35.\n" + 
              "The cost of truck 3 after " + years + " years is $54586.77.\n" + 
              "Next year's maintenance will be $2708.68.\n" + 
              "\nAt $54586.77, truck 3 is the best investment after " + years + " years.\n")
        print("\nAutograder Feedback:\n")

        score = 100

        #input
        score -= check(r'Please input the initial costs of the three trucks:',
                       "Error in initial costs input line", output, 3)          
        score -= check(r'Please input the initial yearly maintenance costs of the three trucks:',
                       "Error yearly maintenance input line", output, 3)
        score -= check(r'Please input the project lifespan in years:',
                       "Error in lifespan input line", output, 4)

        #mid way printing
        score -= check(r'The cost of truck 1 after 12 years is \$31384',
                       "Error in truck 1 half lifespan cost line", output, 5)    
        score -= check(r'Next year\'s maintenance will be \$3138.4',
                       "Error in truck 1 half lifespan maintenance line", output, 5)                 

        score -= check(r'The cost of truck 2 after 12 years is \$30692',
                       "Error in truck 2 half lifespan cost line", output, 5)
        score -= check(r'Next year\'s maintenance will be \$1569.2',
                       "Error in truck 2 half lifespan maintenance line", output, 5)       

        score -= check(r'The cost of truck 3 after 12 years is \$35346',
                       "Error in truck 3 half lifespan cost line", output, 5)  
        score -= check(r'Next year\'s maintenance will be \$784.61.',
                       "Error in truck 3 half lifespan maintenance line", output, 5)                      

        score -= check(r'truck 2 is the best investment after 12 years.',
                       "Error in half lifespan best investment line", output, 15)

        #final printing
        score -= check(r'The cost of truck 1 after 25 years is \$10834',
                       "Error in truck 1 lifespan cost line", output, 5)    
        score -= check(r'Next year\'s maintenance will be \$10834',
                       "Error in truck 1 lifespan maintenance line", output, 5)                 

        score -= check(r'The cost of truck 2 after 25 years is \$69173',
                       "Error in truck 2 lifespan cost line", output, 5)
        score -= check(r'Next year\'s maintenance will be \$5417.3',
                       "Error in truck 2 lifespan maintenance line", output, 5)       

        score -= check(r'The cost of truck 3 after 25 years is \$54586',
                       "Error in truck 3 lifespan cost line", output, 5)  
        score -= check(r'Next year\'s maintenance will be \$2708.6',
                       "Error in truck 3 lifespan maintenance line", output, 5)                      

        score -= check(r'truck 3 is the best investment after 25 years.',
                       "Error in lifespan best investment line", output, 15)

        # Set Test Case Score
        print('Score: ' + str(score) + '%')
        score /= 25
        set_score(score)

        test.terminate()
        cat.terminate()

