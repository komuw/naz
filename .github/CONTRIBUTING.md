Thank you for thinking of contributing to naz.                    
Every contribution to naz is important to us.                       
You may not know it, but you are about to contribute towards making the world a more safer and secure place.                         

Contributor offers to license certain software (a “Contribution” or multiple
“Contributions”) to naz, and naz agrees to accept said Contributions,
under the terms of the MIT License.
Contributor understands and agrees that naz shall have the irrevocable and perpetual right to make
and distribute copies of any Contribution, as well as to create and distribute collective works and
derivative works of any Contribution, under the MIT License.


## To contribute:            

- fork this repo.
- cd naz
- sudo apt-get install pandoc
- open an issue on this repo. In your issue, outline what it is you want to add and why.
- install pre-requiste software:             
```shell
apt-get -y install pandoc && pip install -e .[dev,test]
```                   
- make the changes you want on your fork.
- your changes should have backward compatibility in mind unless it is impossible to do so.
- add your name and contact(optional) to CONTRIBUTORS.md
- add tests
- format your code using [autopep8](https://pypi.python.org/pypi/autopep8):                      
```shell
autopep8 --experimental --in-place -r -aaaaaaaaaaa .
```                     
- run [flake8](https://pypi.python.org/pypi/flake8) on the code and fix any issues:                      
```shell
flake8 .
```                      
- run [pylint](https://pypi.python.org/pypi/pylint) on the code and fix any issues:                      
```shell
pylint --enable=E --disable=W,R,C naz/
```    
- run tests and make sure everything is passing:
```shell
make test
```
- open a pull request on this repo.          
          
NB: I make no commitment of accepting your pull requests.                 
