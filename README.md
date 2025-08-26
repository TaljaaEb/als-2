![alt text](https://github.com/TaljaaEb/als-2/blob/main/ALS-Triple-Validation.png?raw=true)
```
Testing on one machine:
-----------------------
/project-root/
   manage.py
   store/
      views.py
      ...
   monitors/
      a_sql_monitor.py
      b_collector_monitor.py
      c_compare_logger.py
      system_logger.py
      payment_cstring.txt
      payment_data.lock
      
Run Django from /project-root/
Run A, B, C from /project-root/monitors/

```
