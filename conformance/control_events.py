#!/usr/bin/env python3.10

'''
Simple runner for message network tests
'''

import check_ev10_ida
import check_ev20_idg

def prompt() :
    print("\nEvent Exchange Standard testing")
    print(" 0 Run all in sequence")
    print(" 1 Identify Event Addressed testing")
    print(" 2 Identify Event Global testing")
    print("  ")
    print(" q go back")

def testAll() :
    result = 0
 
    print("\nIdentify Event Addressed testing")
    result += check_ev10_ida.test()

    print("\nIdentify Event Global testing")
    result += check_ev20_idg.test()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one test failed")
    
def main() :
    '''
    loop to test against Message Network Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nIdentify Event Addressed testing")
                check_ev10_ida.test()
            case "2" :
                print("\nIdentify Event Global testing")
                check_ev20_idg.test()
           
            case  "0" :
                testAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
