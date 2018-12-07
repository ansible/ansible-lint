
.. _lint_default_rules:

*************
Default Rules
*************

.. contents:: Topics

The table below shows the the default rules used by Ansible Lint to evaluate playbooks and roles:

========================================================== ========================================================== 
ID                                                         Description                                                
========================================================== ========================================================== 
**E1xx**                                                   **Deprecated**                                               
E101                                                       Deprecated always_run                                      
E102                                                       No Jinja2 in when                                          
E103                                                       Deprecated sudo                                            
E104                                                       Using bare variables is deprecated                         
E105                                                       Deprecated module                                          
                                                                                                                      
**E2xx**                                                   **Formatting**                                               
E201                                                       Trailing whitespace                                        
E202                                                       Octal file permissions must contain leading zero           
E203                                                       Most files should not contain tabs                         
E204                                                       Lines must be no longer than 120 chars                   
E205                                                       Playbooks must have the ".yml" extension                 
E206                                                       Variables must have spaces after {{ and before }}        
                                                                                                                      
**E3xx**                                                   **Command and shell modules**                                     
E301                                                       Commands must not change things if nothing needs doing   
E302                                                       Using command rather than an argument to e.g. file         
E303                                                       Using command rather than module                           
E304                                                       Environment variables don't work as part of command        
E305                                                       Use shell only when shell functionality is required        
                                                                                                                      
**E4xx**                                                   **Module**                                                   
E401                                                       Git checkouts must contain explicit version                
E402                                                       Mercurial checkouts must contain explicit revision         
E403                                                       Package installs must not use latest                     
E404                                                       Doesn't need a relative path in role                       
E405                                                       Remote package tasks should have a retry                   
                                                                                                                      
**E5xx**                                                   **Task**                                                     
E501                                                       become_user requires become to work as expected            
E502                                                       All tasks must be named                                  
E503                                                       Tasks that run when changed should likely be handlers      
E504                                                       Do not use 'local_action', use 'delegate_to: localhost'    
                                                                                                                      
**E6xx**                                                   **Idiom**                                                    
E601                                                       Don't compare to literal True/False                        
E602                                                       Don't compare to empty string                              
                                                                                                                      
**E7xx**                                                   **Metadata**                                                 
E701                                                       meta/main.yml must contain relevant info                 
E702                                                       Tags must contain lowercase letters and digits only        
E703                                                       meta/main.yml default values must be changed             
E704                                                       meta/main.yml video_links must be formatted correctly    
========================================================== ========================================================== 
