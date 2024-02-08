#!/usr/bin/env python3.10

'''
Simple runner for frame transport suite
'''

import check_fr10_init

def prompt() :
    print("\nFrame Transport Standard testing")
    print(" 0 Run all in sequence")
    print(" 1 Initialization testing")
    print("  ")
    print(" q go back")

def testAll() :
    result = 0
 
    print("\nInitialization testing")
    result += check_fr10_init.test()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one test failed")
        
    return result
    
def main() :
    '''
    loop to test against Frame Transport Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nInitialization testing")
                check_fr10_init.test()
           
            case  "0" :
                testAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
