Contributing to Ansible-lint
============================

To contribute to ansible-lint, please use pull requests on a branch of your own fork
After creating your fork on github, you can do
```
git clone git@github.com:yourname/ansible-lint
cd ansible-lint
git checkout -b your-branch-name
DO SOME CODING HERE
git add your new files
git commit
git push origin your-branch-nane
```
You will then be able to create a pull request from your commit. 

All fixes to core functionality (i.e. anything except rules or examples) should
be accompanied by tests that fail prior to your change and succeed afterwards. 

Feel free to raise issues in the repo if you don't feel able to contribute a code fix.
