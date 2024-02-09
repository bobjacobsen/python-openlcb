#!/usr/bin/env python3.10

'''
Simple runner for message network checks
'''

import check_me10_init
import check_me20_verify
import check_me30_pip
import check_me40_oir
import check_me50_dup

def prompt() :
    print("\nMessage Network Standard checking")
    print(" 0 Run all in sequence")
    print(" 1 Node Initialized checking")
    print(" 2 Verify Node checking")
    print(" 3 Protocol Support Inquiry checking")
    print(" 4 Optional Interaction Rejected checking")
    print(" 5 Duplicate Node ID Discovery checking")
    print("  ")
    print(" q go back")

def checkAll() :
    result = 0
 
    print("\nNode Initialized checking")
    result += check_me10_init.check()

    print("\nVerify Node checking")
    result += check_me20_verify.check()

    print("\nProtocol Support Inquiry checking")
    result += check_me30_pip.check()

    print("\nOptional Interaction Rejected checking")
    result += check_me40_oir.check()

    print("\nDuplicate Node ID Discovery checking")
    result += check_me50_dup.check()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one check failed")

    return result
    
def main() :
    '''
    loop to check against Message Network Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nNode Initialized checking")
                check_me10_init.check()
            case "2" :
                print("\nVerify Node checking")
                check_me20_verify.check()
            case "3" :
                print("\nProtocol Support Inquiry checking")
                check_me30_pip.check()
            case "4" :
                print("\nOptional Interaction Rejected checking")
                check_me40_oir.check()
            case "5" :
                print("\nDuplicate Node ID Discovery checking")
                check_me50_dup.check()
           
            case  "0" :
                checkAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
