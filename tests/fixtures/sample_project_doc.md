# Acme Toolkit

Acme Toolkit is a data-processing library first released in 2019.
It requires Python 3.11 or higher. The default request timeout is 60 seconds.

We think it is the most pleasant toolkit to use, and you will probably love it.

## Configuration

The batch size defaults to 100 records per call. Larger batches use more memory.

```python
# Example only -- not a real project claim.
default_timeout = 30
batch_size = 500
```

See Dr. Rivera's benchmark, e.g. the 2021 report, for performance numbers.
