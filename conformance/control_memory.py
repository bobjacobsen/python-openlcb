#!/usr/bin/env python3.10

'''
Simple runner for Memory Configuration suite
'''

import check_mc10_co
import check_mc20_ckasi

def prompt() :
    print("\nMemory Configuration Standard testing")
    print(" 0 Run all in sequence")
    print(" 1 Configuration Options testing")
    print(" 2 Address Space Information testing")
    print("  ")
    print(" q go back")

def testAll() :
    result = 0
 
    print("\nConfiguration Options testing")
    result += check_mc10_co.test()

    print("\nAddress Space Information testing")
    result += check_mc20_ckasi.test()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one test failed")
        
    return result
    
def main() :
    '''
    loop to test against SNIP Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nConfiguration Options testing")
                check_mc10_co.test()

            case "2" : 
                print("\nAddress Space Information testing")
                check_mc20_ckasi.test()
           
            case  "0" :
                testAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
