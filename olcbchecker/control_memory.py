#!/usr/bin/env python3.10

'''
Simple runner for Memory Configuration suite
'''

import check_mc10_co
import check_mc20_ckasi

def prompt() :
    print("\nMemory Configuration Standard checking")
    print(" 0 Run all in sequence")
    print(" 1 Configuration Options checking")
    print(" 2 Address Space Information checking")
    print("  ")
    print(" q go back")

def checkAll() :
    result = 0
 
    print("\nConfiguration Options checking")
    result += check_mc10_co.check()

    print("\nAddress Space Information checking")
    result += check_mc20_ckasi.check()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one check failed")
        
    return result
    
def main() :
    '''
    loop to check against SNIP Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nConfiguration Options checking")
                check_mc10_co.check()

            case "2" : 
                print("\nAddress Space Information checking")
                check_mc20_ckasi.check()
           
            case  "0" :
                checkAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
