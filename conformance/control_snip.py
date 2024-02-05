#!/usr/bin/env python3.10

'''
Simple runner for SNIP suite
'''

import check_sn10_snip

def prompt() :
    print("\nSNIP Standard testing")
    print(" 0 Run all in sequence")
    print(" 1 SNIP reply testing")
    print("  ")
    print(" q go back")

def testAll() :
    result = 0
 
    print("\nSNIP reply testing")
    result += check_sn10_snip.test()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one test failed")
    
def main() :
    '''
    loop to test against SNIP Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nSNIP reply testing")
                check_sn10_snip.test()
           
            case  "0" :
                testAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
