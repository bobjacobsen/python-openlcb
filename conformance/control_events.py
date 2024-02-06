#!/usr/bin/env python3.10

'''
Simple runner for message network tests
'''

import check_ev10_ida
import check_ev20_idg
import check_ev30_ip
import check_ev40_ic

def prompt() :
    print("\nEvent Exchange Standard testing")
    print(" 0 Run all in sequence")
    print(" 1 Identify Event Addressed testing")
    print(" 2 Identify Event Global testing")
    print(" 3 Identify Producer testing")
    print(" 4 Identify Consumer testing")
    print("  ")
    print(" q go back")

def testAll() :
    result = 0
 
    print("\nIdentify Event Addressed testing")
    result += check_ev10_ida.test()

    print("\nIdentify Event Global testing")
    result += check_ev20_idg.test()

    print("\nIdentify Producer testing")
    result += check_ev30_ip.test()

    print("\nIdentify Consumer testing")
    result += check_ev40_ic.test()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one test failed")

    return result
    
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
            case "3" : 
                print("\nIdentify Producer testing")
                check_ev30_ip.test()
            case "4" :
                print("\nIdentify Consumer testing")
                check_ev40_ic.test()
           
            case  "0" :
                testAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
