Thank you for thinking of contributing to naz.                    
Every contribution to naz is important.                       
                         

Contributions are under the [MIT License](https://github.com/komuw/naz/blob/master/LICENSE.txt).


## To contribute:            

- open a [github issue](https://github.com/komuw/naz/issues) to first discuss the change you want to make.
- once the github issue has been discussed and approved, you can now proceeds
- fork this repo.
- install pre-requiste software:             
```shell
apt-get -y install pandoc && pip install -e .[dev,test,benchmarks]
```                   
- make the changes you want on your fork.
- your changes should have backward compatibility in mind unless it is impossible to do so.
- add tests
- format your code using [black](https://github.com/ambv/black):                      
```shell
black --line-length=100 .
```                     
- run `make test` on the code and fix any issues:                      
- open a pull request on this repo.          
          
NB: I make no commitment of accepting your pull requests.                 
