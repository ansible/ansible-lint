| id                                                       | sample message                                           |
|----------------------------------------------------------|----------------------------------------------------------|
| **E1**                                                   | *deprecated*                                             |
| E101                                                     | Deprecated always_run                                    |
| E102                                                     | No Jinja2 in when                                        |
| E103                                                     | Deprecated sudo                                          |
| E104                                                     | Using bare variables is deprecated                       |
|                                                          |                                                          |
| **E2**                                                   | *formatting*                                             |
| E201                                                     | Trailing whitespace                                      |
| E202                                                     | Octal file permissions must contain leading zero         |
|                                                          |                                                          |
| **E3**                                                   | *command-shell*                                          |
| E301                                                     | Commands should not change things if nothing needs doing |
| E302                                                     | Using command rather than an argument to e.g. file       |
| E303                                                     | Using command rather than module                         |
| E304                                                     | Environment variables don't work as part of command      |
| E305                                                     | Use shell only when shell functionality is required      |
|                                                          |                                                          |
| **E4**                                                   | *module*                                                 |
| E401                                                     | Git checkouts must contain explicit version              |
| E402                                                     | Mercurial checkouts must contain explicit revision       |
| E403                                                     | Package installs should not use latest                   |
|                                                          |                                                          |
| **E5**                                                   | *task*                                                   |
| E501                                                     | become_user requires become to work as expected          |
| E502                                                     | All tasks should be named                                |
| E503                                                     | Tasks that run when changed should likely be handlers    |
