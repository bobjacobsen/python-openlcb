#!/usr/bin/env python3.10

'''
Simple runner for message network tests
'''

import check_me10_init
import check_me20_verify
import check_me30_pip
import check_me40_oir
import check_me50_dup

def prompt() :
    print("\nMessage Network Standard testing")
    print(" 0 Run all in sequence")
    print(" 1 Node Initialized testing")
    print(" 2 Verify Node testing")
    print(" 3 Protocol Support Inquiry testing")
    print(" 4 Optional Interaction Rejected testing")
    print(" 5 Duplicate Node ID Discovery testing")
    print("  ")
    print(" q go back")

def testAll() :
    result = 0
 
    print("\nNode Initialized testing")
    result += check_me10_init.test()

    print("\nVerify Node testing")
    result += check_me20_verify.test()

    print("\nProtocol Support Inquiry testing")
    result += check_me30_pip.test()

    print("\nOptional Interaction Rejected testing")
    result += check_me40_oir.test()

    print("\nDuplicate Node ID Discovery testing")
    result += check_me50_dup.test()

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
                print("\nNode Initialized testing")
                check_me10_init.test()
            case "2" :
                print("\nVerify Node testing")
                check_me20_verify.test()
            case "3" :
                print("\nProtocol Support Inquiry testing")
                check_me30_pip.test()
            case "4" :
                print("\nOptional Interaction Rejected testing")
                check_me40_oir.test()
            case "5" :
                print("\nDuplicate Node ID Discovery testing")
                check_me50_dup.test()
           
            case  "0" :
                testAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
