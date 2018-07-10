pip install -U jupyter jupyterlab      
jupyter lab -y 
jupyter nbconvert pres.ipynb --to slides --post serve --SlidesExporter.reveal_theme=serif --SlidesExporter.reveal_scroll=True --SlidesExporter.reveal_transition=none    


# topics                   
1. SMPP spec intro               
2. SMPP & python intro        
3. current lay of the land          
    3.1 problems with current solutions           
4. naz intro                     
    4.1 architecture              
    4.2 usage                    
5. naz features         
    5.1 async           
    5.2 observability            
    5.3 Rate limiting             
    5.4 Throttle handling              
    5.5 Queuing            
6. then what?  

## 1. SMPP spec intro                 
The SMPP protocol is an open protocl designed for transfer of short message data between a Message Center(SMSC/USSD server etc) & a SMS application system.                
SMPP is based on the exchange of request and response protocol data units(PDUs) between the client/ESME and the server/SMSC over an underlying TCP/IP network connection.                


| CLIENT |&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | SERVER/smsc | &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | PHONE |                         
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1. network connect                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->             

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2. bind_transceiver                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->                    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3. bind_transceiver_resp                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<-----------------------------                 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;4. submit_sm                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->                    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5. submit_sm_resp                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<-----------------------------       &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   send SMS to phone               
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   ---------------------->          

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6. submit_sm                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->           
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;7. submit_sm                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->            
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;8. submit_sm                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->     
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;9. submit_sm                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->                     
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;10. submit_sm_resp                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<-----------------------------   
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;11. submit_sm_resp                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<-----------------------------   

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;12. unbind                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;----------------------------->                    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;13. unbind_resp                
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<-----------------------------                                          


PDU FORMAT:                 
<-----------------------------------------------------HEADER--------------------------------------->                                 
| command_length | command_id | command_status | sequence_number |  body |                     

1. command_length, 4bytes, Integer     
2. command_id, 4bytes, Integer. eg `submit_sm` is command_id 4          
3. command_status, 4bytes, Integer. eg success is integer 0           
4. sequence_number, 4bytes, Integer  



## 2. SMPP & python intro         
```python
import socket
import struct

# 1. network connect
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect(('127.0.0.1', 2775))

# 2. create enquire_link PDU
body = b""
command_length = 16 + len(body)  # 16 is for headers
command_id = 21 # the command_id for `enquire_link` PDU
command_status = 0
sequence_number = 1
header = struct.pack(">IIII", command_length, command_id, command_status, sequence_number)

# send PDU
full_pdu = header + body
sock.send(full_pdu)
```          


## 3. current lay of the land               
- github.com/podshumok/python-smpplib               
- github.com/praekelt/vumi                    
- ... couple more          



#### 3.1 problems with current solutions           
    - complexity of code base    
    - coupling with other things(rabbitMQ, redis, Twisted)      
    - non-granular configurability         
      - (PR #352 to configure what happens when SMSC throttles us, you can only set `throttle_delay: X seconds` )
    - maintenance debt:
      - (PR #342 disable vumi sentry integration; The latest version of vumi has not updated its raven dependancies)
      - upgrade to python3 but transport is yet to(because vumi is py2)
    - lack of visibility      
      - (PR #335 and PR #327 enrich queue to vumi logging). 
      - PR #336, PR #339

## 4. naz intro                     



#### 4.1 architecture              
#### 4.2 usage                    

## 5. naz features        
#### 5.1 async          
#### 5.2 observability         
5.2.1 logging               
5.2.2 hooks         
5.3 Rate limiting             
5.4 Throttle handling              
5.5 Queuing          

6. then what?         


vumi smpp config:     
https://github.com/praekelt/vumi/blob/master/vumi/transports/smpp/config.py
