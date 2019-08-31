Thank you for thinking of contributing to naz.                    
Every contribution to naz is important to.                       
                         

Contributor offers to license certain software (a “Contribution” or multiple
“Contributions”) to naz, and naz agrees to accept said Contributions,
under the terms of the MIT License.
Contributor understands and agrees that naz shall have the irrevocable and perpetual right to make
and distribute copies of any Contribution, as well as to create and distribute collective works and
derivative works of any Contribution, under the MIT License.


## To contribute:            

- fork this repo.
- sudo apt-get install pandoc
- install pre-requiste software:             
```shell
apt-get -y install pandoc && pip install -e .[dev,test,benchmarks]
```                   
- make the changes you want on your fork.
- your changes should have backward compatibility in mind unless it is impossible to do so.
- add tests
- format your code using [black](https://github.com/ambv/black):                      
```shell
black --line-length=100 --target-version py36 .
```                     
- run [flake8](https://pypi.python.org/pypi/flake8) on the code and fix any issues:                      
```shell
flake8 .
```                      
- run [pylint](https://pypi.python.org/pypi/pylint) on the code and fix any issues:                      
```shell
pylint --enable=E --disable=W,R,C naz/ tests/ cli/ documentation/ examples/ benchmarks/
```    
- run bandit
```shell
bandit -r --exclude .venv -ll .
```
- run tests and make sure everything is passing:
```shell
make test
```
- open a pull request on this repo.          
          
NB: I make no commitment of accepting your pull requests.                 
