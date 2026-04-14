import sys

def add_numbers(num1, num2):
    return num1 + num2

def chat():
    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))
    print("The sum of the two numbers is", add_numbers(num1, num2))

def main():
    if __name__ == '__main__':
        chat()
    else:
        test_app()

def test_app():
    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))
    print("The sum of the two numbers is", add_numbers(num1, num2))

if __name__ == '__main__':
    main()