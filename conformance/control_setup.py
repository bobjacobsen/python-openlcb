#!/usr/bin/env python3.10

'''
Simple runner for SNIP suite
'''

import os

literals = ["portnumber", "trace", "checkpip"] # store without quotes, e.g. store the literal value

def main() :
    # start by getting the current defaults
    # note that 'import' only works the first time; after that, we keep these in variables.
    exec(compile(open("./defaults.py").read(), "./defaults.py", 'exec'))
    if os.path.isfile("./localoverrides.py") :
        try :
            exec(compile(open("./localoverrides.py").read(), "./localoverrides.py", 'exec'))
        except :
            print("*** Unable to read the local override configuration from the localoverrides.py file.  ***")
            print("*** Continuing without your local configuration.  Please reconfigure to resolve this. ***\n")
    local_variables = {}
    temp_list = locals()
    for temp_item in temp_list.keys():
        local_variables[temp_item] = temp_list[temp_item]
    del local_variables['local_variables']
        
    settings_changed = False
    
    while True:
        print("The current settings are:")
        for s in local_variables.keys() :
            print ("  {} = {}".format(s, local_variables.get(s)))

        if ('devicename' not in local_variables or local_variables['devicename'] == None) and ('hostname' not in local_variables or local_variables['hostname'] == None) :
            print("\nPlease provide either hostname or devicename")
        print ("\nc change setting\nh help\nr return\n")
        match input(">> ") :
            case "c" :
                variable = input("enter variable name\n>> ")
                if variable == "" : continue # if you don't enter a variable, go back and avoid error
                settings_changed = True

                value = input("enter new value\n>> ")
                if value == "" :
                    exec("local_variables['{}'] = None".format(variable))
                else : 
                    exec("local_variables['{}'] = '{}'".format(variable, value))
                
                # special case of "only one"
                
                                    
            case "r" | "q":
                if settings_changed: 
                    if input("\nDo you want to save the new settings? (y/n)\n >> ") == "y" :
                        f = open("localoverrides.py", "w")
                        for s in local_variables.keys() :
                            if s in literals or local_variables.get(s) == "None" or local_variables.get(s) == None:
                                f.write ("{} = {}\n".format(s, local_variables.get(s)))
                            else:
                                f.write ('{} = "{}"\n'.format(s, local_variables.get(s)))                            
                        f.close()
                        print("Stored\nQuit and restart the program to put them into effect")
                    else :
                        print("Not stored\n")
                return

            case "h" :

                print('Exactly one of hostname or deviceanme must be provided.')
                print('   hostname e.g. localhost or 192.168.21.3 specifies a GridConnect TCP connection')
                print('      hostname can be accompanied by portnumber, which defaults to 12021')
                print('   devicename e.g. /dev/cu-USBserial specifies a serial port connection')
                print('')
                print('targetnodeid is the ID of the node to be tested.')
                print('    A value of None means get it from the node itself; this only works for single nodes')
                print('    ')
                print('trace defines the level of output. Higher numbers are more output:')
                print('    0 only failures and errors')
                print('   10 plus success info messages')
                print('   20 plus message traces')
                print('   30 plus frame level traces')
                print('   40 plus serial level traces')
                print('   50 plus internal code traces')
                print('') 
                    
            case _ : continue



if __name__ == "__main__":
    main()
