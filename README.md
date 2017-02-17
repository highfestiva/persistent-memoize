# Persisted "background" memoization

This module will save your memoized values to file on disk, so the values
won't have to be recalculated when the application is restarted.

It also supports background calculations, and will return extrapolated
values while a background thread does the calculations. This is useful if
your calculations are slow but your front-end expects updates right away.

Everything wrapped up in a nice decorator. You can set the maximum number
of values you want to memoize, and the extrapolation function if you like.

```python
from persistent_memoize import *

@persistent_background_memoize('/tmp/somefile')
def func(n):
    # Do something slow instead...
    return n*3

[func(1) for _ in range(10)]
```
